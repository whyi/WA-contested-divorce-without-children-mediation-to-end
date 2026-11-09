import io
import logging
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from botocore.exceptions import BotoCoreError
from fastapi import HTTPException, Response
from fastapi.testclient import TestClient

from app.analysis_worker import AnalysisLease, process_analysis_job
from app.config import Settings, provider_data_handling_notice
from app.failure_logging import log_failure_event
from app.main import app, retry_case_document_extraction, support_configuration


class FailureRecoveryUiTests(unittest.TestCase):
    page = open("src/app/static/index.html", encoding="utf-8").read()

    def test_direct_creation_preserves_in_page_retry_and_legacy_offer_recovery(self) -> None:
        self.assertIn('caseCreateProgressStorageKey = "case-create-progress"', self.page)
        self.assertIn("caseCreateProgress = { caseId, mode }", self.page)
        self.assertIn("let caseId = caseCreateProgress?.caseId || null", self.page)
        self.assertIn("sessionStorage.getItem(caseCreateProgressStorageKey", self.page)

    def test_existing_offer_upload_and_notes_survive_reload(self) -> None:
        self.assertIn("existingOfferRecoveryKey", self.page)
        self.assertIn("restoreExistingOfferRecovery", self.page)
        self.assertIn("sessionStorage.setItem(existingOfferRecoveryKey", self.page)
        self.assertIn("sameFileIdentity", self.page)
        self.assertIn("reselect the same file to retry", self.page.lower())
        self.assertNotIn("function applyExistingOfferGate", self.page)
        self.assertIn("file bytes are not retained by the browser", self.page)

    def test_failure_messages_cover_processing_and_final_download_recovery(self) -> None:
        for recovery_text in (
            "Previous upload status could not be verified",
            "The file was not imported. Retry with the same selected file.",
            "Retry failed file import",
            "Retry failed file import",
            "Copy safe diagnostic details",
            "Contact support",
        ):
            with self.subTest(recovery_text=recovery_text):
                self.assertIn(recovery_text, self.page)
        helper = self.page.split("function addFailureSupportActions", 1)[1].split(
            "async function settlementApi", 1
        )[0]
        self.assertIn("Observed at (UTC)", helper)
        self.assertIn("HTTP status", helper)
        self.assertIn("Error code", helper)
        self.assertNotIn("filename", helper.lower())
        self.assertNotIn("case_id", helper.lower())
        self.assertIn("caseImportIdentities", self.page)
        self.assertIn("identity.documentId", self.page)
        self.assertIn("pending.length > config.max_attachments", self.page)

    def test_support_configuration_is_optional_and_not_cached(self) -> None:
        settings = SimpleNamespace(support_contact_url=None)
        response = Response()

        with patch("app.main.settings", settings):
            result = support_configuration(response)

        self.assertEqual(result, {"contact_url": None})
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_support_configuration_route_exposes_only_the_operator_url(self) -> None:
        settings = SimpleNamespace(
            support_contact_url="https://support.example.test/contact",
            auth_enabled=False,
            case_data_enabled=False,
        )
        with patch("app.main.settings", settings):
            response = TestClient(app).get("/api/v1/support/config")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"contact_url": "https://support.example.test/contact"},
        )
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_failure_log_omits_exception_text_and_sensitive_values(self) -> None:
        stream = io.StringIO()
        logger = logging.getLogger(f"failure-test-{uuid4()}")
        logger.setLevel(logging.ERROR)
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)
        try:
            log_failure_event(
                logger,
                "proposal_generation_failed",
                RuntimeError("sensitive.pdf token=private-text"),
            )
        finally:
            logger.removeHandler(handler)

        message = stream.getvalue()
        self.assertIn("event_code=proposal_generation_failed", message)
        self.assertIn("error_type=RuntimeError", message)
        self.assertNotIn("sensitive.pdf", message)
        self.assertNotIn("private-text", message)


class AnalysisFailureTests(unittest.TestCase):
    def test_provider_failure_is_persisted_as_failed_without_empty_success(self) -> None:
        case_id, user_id, request_id, consent_id, document_id = (uuid4() for _ in range(5))
        digest = "c" * 64
        token = uuid4()
        job = SimpleNamespace(
            id=uuid4(),
            request_id=request_id,
            document_id=document_id,
            source_sha256=digest,
            status="processing",
            lease_token=token,
            error_code=None,
            lease_expires_at=None,
            completed_at=None,
        )
        request = SimpleNamespace(
            id=request_id,
            case_id=case_id,
            user_id=user_id,
            consent_id=consent_id,
            status="processing",
        )
        consent = SimpleNamespace(
            id=consent_id,
            request_id=request_id,
            case_id=case_id,
            user_id=user_id,
            revoked_at=None,
            notice_version="notice-1",
            model_id="test-model",
            region="us-west-2",
            data_handling_notice=provider_data_handling_notice("Retention notice."),
        )
        document = SimpleNamespace(id=document_id, case_id=case_id, sha256=digest)
        extraction_job = SimpleNamespace(
            document_id=document_id,
            source_sha256=digest,
            status="completed",
        )
        extraction = SimpleNamespace(
            extracted_text="Source text.",
            pages_json=[{"page_number": 1, "text": "Source text."}],
        )
        db = Mock()
        db.get.side_effect = [job, request, document, job, request]
        db.scalar.side_effect = [
            consent,
            SimpleNamespace(role="owner"),
            None,
            None,
            None,
            extraction_job,
            extraction,
        ]
        db.scalars.return_value.all.return_value = ["failed"]
        client = Mock()
        client.converse.side_effect = BotoCoreError()
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="secure-test-analysis-signing-key-that-is-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_endpoint_url="http://localhost:5000",
            ai_analysis_enabled=True,
            ai_analysis_notice_version="notice-1",
            ai_analysis_data_handling_notice="Retention notice.",
            bedrock_model_id="test-model",
            bedrock_region="us-west-2",
        )

        process_analysis_job(
            db,
            AnalysisLease(job.id, token),
            settings=settings,
            client=client,
        )

        self.assertEqual(job.status, "failed")
        self.assertEqual(job.error_code, "provider_unavailable")
        self.assertEqual(request.status, "failed")
        self.assertEqual(document.sha256, digest)
        db.add.assert_not_called()
        db.commit.assert_called_once()


class ExtractionRetryRouteTests(unittest.TestCase):
    def test_failed_extraction_job_has_an_authenticated_retry_route(self) -> None:
        routes = {
            (route.path, method)
            for route in app.routes
            for method in getattr(route, "methods", set())
        }
        self.assertIn(
            (
                "/cases/{case_id}/documents/{document_id}/extraction-jobs/{job_id}/retry",
                "POST",
            ),
            routes,
        )

    def test_retry_route_requires_case_authentication(self) -> None:
        settings = SimpleNamespace(
            auth_enabled=True,
            auth_jwt_secret="failure-recovery-auth-secret-that-is-long-enough",
            case_data_enabled=True,
        )
        path = (
            f"/cases/{uuid4()}/documents/{uuid4()}/extraction-jobs/{uuid4()}/retry"
        )
        with patch("app.main.settings", settings):
            response = TestClient(app).post(path)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication required.")

    def test_failed_extraction_is_explicitly_retryable_in_the_ui(self) -> None:
        self.assertNotIn('id="analysis-controls"', FailureRecoveryUiTests.page)
        self.assertNotIn("function retryDocumentExtraction", FailureRecoveryUiTests.page)

    def test_retry_requeues_only_matching_failed_source_and_reports_no_store(self) -> None:
        case_id, document_id, job_id, request_id = (uuid4() for _ in range(4))
        digest = "a" * 64
        document = SimpleNamespace(id=document_id, case_id=case_id, sha256=digest)
        job = SimpleNamespace(
            id=job_id,
            document_id=document_id,
            source_sha256=digest,
            request_id=request_id,
            status="failed",
            error_code="storage_unavailable",
        )
        db = Mock()
        db.get.side_effect = [document, job]
        response = Response()

        def requeue(*_args):
            job.status = "queued"
            job.error_code = None
            return job

        with patch("app.main.retry_failed_extraction_job", side_effect=requeue) as retry:
            result = retry_case_document_extraction(
                case_id, document_id, job_id, response, db
            )

        self.assertEqual(result.status, "queued")
        self.assertEqual(result.job_id, job_id)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        retry.assert_called_once_with(db, job_id, request_id)

    def test_retry_rejects_nonfailed_jobs_without_mutation(self) -> None:
        case_id, document_id, job_id = (uuid4() for _ in range(3))
        digest = "b" * 64
        document = SimpleNamespace(id=document_id, case_id=case_id, sha256=digest)
        job = SimpleNamespace(
            id=job_id,
            document_id=document_id,
            source_sha256=digest,
            status="completed",
        )
        db = Mock()
        db.get.side_effect = [document, job]

        with self.assertRaises(HTTPException) as raised:
            retry_case_document_extraction(case_id, document_id, job_id, Response(), db)

        self.assertEqual(raised.exception.status_code, 409)
        db.commit.assert_not_called()

    def test_retry_limit_returns_actionable_conflict_and_keeps_source(self) -> None:
        case_id, document_id, job_id = (uuid4() for _ in range(3))
        digest = "c" * 64
        document = SimpleNamespace(id=document_id, case_id=case_id, sha256=digest)
        job = SimpleNamespace(
            id=job_id,
            document_id=document_id,
            source_sha256=digest,
            request_id=uuid4(),
            status="failed",
            attempts=4,
        )
        db = Mock()
        db.get.side_effect = [document, job]
        response = Response()

        with patch("app.main.retry_failed_extraction_job", return_value=job):
            with self.assertRaises(HTTPException) as raised:
                retry_case_document_extraction(
                    case_id, document_id, job_id, response, db
                )

        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn("3 retries", raised.exception.detail)
        self.assertIn("source remains stored", raised.exception.detail)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        db.delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
