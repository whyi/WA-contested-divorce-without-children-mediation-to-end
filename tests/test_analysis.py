import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from app.analysis import (
    AnalysisRequestCreate,
    aggregate_analysis_status,
    analysis_disclosure,
    create_analysis_request,
    is_analysis_available,
    retry_analysis_job,
    revoke_analysis_consent,
)
from app.config import Settings
from app.settlement_routes import ConsentCreate


class AnalysisConfigurationTests(unittest.TestCase):
    def test_analysis_is_unavailable_by_default(self) -> None:
        self.assertFalse(is_analysis_available(Settings()))
        self.assertFalse(analysis_disclosure(Settings()).available)

    def test_analysis_requires_provider_region_and_deployment_notice(self) -> None:
        base = {
            "auth_enabled": True,
            "auth_jwt_secret": "secure-test-analysis-signing-key-that-is-long-enough",
            "case_data_enabled": True,
            "case_materials_enabled": True,
            "s3_endpoint_url": "http://localhost:5000",
            "ai_analysis_enabled": True,
            "bedrock_model_id": "test-model",
            "bedrock_region": "us-west-2",
            "ai_analysis_notice_version": "notice-1",
            "ai_analysis_data_handling_notice": "Provider retention is configured by deployment.",
        }
        self.assertTrue(is_analysis_available(Settings(**base)))

        for missing in (
            "bedrock_model_id",
            "bedrock_region",
            "ai_analysis_notice_version",
            "ai_analysis_data_handling_notice",
        ):
            settings = {**base, missing: None}
            with self.subTest(missing=missing):
                self.assertFalse(is_analysis_available(Settings(**settings)))

    def test_disclosure_names_provider_model_purpose_and_data_handling(self) -> None:
        disclosure = analysis_disclosure(
            Settings(
                ai_analysis_enabled=True,
                bedrock_model_id="test-model",
                bedrock_region="us-west-2",
                ai_analysis_notice_version="notice-1",
                ai_analysis_data_handling_notice="Deployment retention notice.",
            )
        )

        self.assertEqual(disclosure.provider, "Amazon Bedrock")
        self.assertEqual(disclosure.model_id, "test-model")
        self.assertEqual(disclosure.region, "us-west-2")
        self.assertIn("documents you select", disclosure.data_sent)
        self.assertIn("Deployment retention notice.", disclosure.data_handling_notice)
        self.assertIn("human access or review", disclosure.data_handling_notice)
        self.assertIn("generalized model training", disclosure.data_handling_notice)

    def test_analysis_requires_the_complete_production_readiness_gate(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="secure-test-analysis-signing-key-that-is-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_endpoint_url="https://s3.example.test",
            s3_kms_key_id="arn:aws:kms:us-west-2:123:key/test",
            ai_analysis_enabled=True,
            bedrock_model_id="test-model",
            bedrock_region="us-west-2",
            ai_analysis_notice_version="notice-1",
            ai_analysis_data_handling_notice="Provider-specific facts.",
            production_readiness_required=True,
            counsel_review_evidence_verified=True,
            ai_provider_review_evidence_verified=True,
        )
        self.assertFalse(is_analysis_available(settings))
        self.assertFalse(analysis_disclosure(settings).available)

    def test_analysis_consent_schema_rejects_reuse_as_training_consent(self) -> None:
        with self.assertRaises(ValidationError):
            AnalysisRequestCreate(
                idempotency_key=uuid4(),
                document_ids=[uuid4()],
                notice_version="notice-1",
                consent=True,
                training_consent=True,
            )
        with self.assertRaises(ValidationError):
            ConsentCreate(
                confirm=True,
                notice_version="settlement-planning-v1",
                training_consent=True,
            )

    def test_analysis_request_persists_consent_and_one_job_per_eligible_file(self) -> None:
        case_id = uuid4()
        user_id = uuid4()
        document_id = uuid4()
        digest = "a" * 64
        document = SimpleNamespace(
            id=document_id,
            case_id=case_id,
            sha256=digest,
        )
        extraction_job = SimpleNamespace(status="completed", source_sha256=digest)
        extraction = SimpleNamespace(extracted_text="A supported fact.")
        db = Mock()
        db.get.return_value = None
        db.scalars.return_value.all.return_value = [document]
        db.scalar.side_effect = [extraction_job, extraction]
        payload = AnalysisRequestCreate(
            idempotency_key=uuid4(),
            document_ids=[document_id],
            notice_version="notice-1",
            consent=True,
        )

        request = create_analysis_request(
            db,
            case_id,
            user_id,
            payload,
            enabled_settings(),
        )

        consent, saved_request, job = db.add_all.call_args.args[0]
        self.assertEqual(request.id, payload.idempotency_key)
        self.assertEqual(saved_request.consent_id, consent.id)
        self.assertEqual(consent.user_id, user_id)
        self.assertEqual(consent.notice_version, "notice-1")
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.source_sha256, digest)
        db.commit.assert_called_once()

    def test_analysis_request_rejects_unprocessed_documents_without_queueing(self) -> None:
        db = Mock()
        db.get.return_value = None
        db.scalars.return_value.all.return_value = [
            SimpleNamespace(id=uuid4(), sha256="b" * 64)
        ]
        db.scalar.return_value = None
        payload = AnalysisRequestCreate(
            idempotency_key=uuid4(),
            document_ids=[db.scalars.return_value.all.return_value[0].id],
            notice_version="notice-1",
            consent=True,
        )

        with self.assertRaises(HTTPException) as raised:
            create_analysis_request(
                db,
                uuid4(),
                uuid4(),
                payload,
                enabled_settings(),
            )

        self.assertEqual(raised.exception.status_code, 409)
        db.add_all.assert_not_called()
        db.commit.assert_not_called()

    def test_retry_only_requeues_a_failed_job_with_active_consent_and_same_source(self) -> None:
        case_id = uuid4()
        request_id = uuid4()
        document_id = uuid4()
        digest = "c" * 64
        request = SimpleNamespace(
            id=request_id,
            case_id=case_id,
            consent_id=uuid4(),
            status="failed",
        )
        consent = SimpleNamespace(
            id=request.consent_id,
            request_id=request_id,
            case_id=case_id,
            revoked_at=None,
        )
        job = SimpleNamespace(
            request_id=request_id,
            document_id=document_id,
            source_sha256=digest,
            status="failed",
            attempts=3,
            error_code="provider_unavailable",
            lease_token=uuid4(),
            lease_expires_at=datetime.now(),
            completed_at=datetime.now(),
        )
        document = SimpleNamespace(id=document_id, case_id=case_id, sha256=digest)
        db = Mock()
        db.scalar.side_effect = [
            request,
            job,
            SimpleNamespace(status="completed"),
            SimpleNamespace(extracted_text="Source text."),
        ]
        db.get.side_effect = [consent, document]

        retried = retry_analysis_job(
            db,
            case_id,
            request_id,
            document_id,
            enabled_settings(),
        )

        self.assertIs(retried, job)
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.attempts, 0)
        self.assertIsNone(job.error_code)
        self.assertEqual(request.status, "queued")
        db.commit.assert_called_once()

    def test_revocation_cancels_queued_jobs_for_the_request(self) -> None:
        case_id = uuid4()
        user_id = uuid4()
        consent_id = uuid4()
        request_id = uuid4()
        queued_job = SimpleNamespace(
            status="queued",
            error_code=None,
            lease_token=uuid4(),
            lease_expires_at=datetime.now(),
            completed_at=None,
        )
        consent = SimpleNamespace(
            id=consent_id,
            request_id=request_id,
            case_id=case_id,
            user_id=user_id,
            revoked_at=None,
        )
        request = SimpleNamespace(id=request_id, status="queued")
        db = Mock()
        db.scalar.side_effect = [consent, request]
        db.scalars.return_value.all.side_effect = [[queued_job], ["cancelled"]]

        revoked_request = revoke_analysis_consent(
            db,
            case_id,
            consent_id,
            user_id,
        )

        self.assertIs(revoked_request, request)
        self.assertIsNotNone(consent.revoked_at)
        self.assertEqual(queued_job.status, "cancelled")
        self.assertEqual(queued_job.error_code, "consent_revoked")
        self.assertEqual(request.status, "cancelled")
        db.commit.assert_called_once()


class AnalysisRequestValidationTests(unittest.TestCase):
    def test_request_requires_explicit_consent_and_unique_documents(self) -> None:
        document_id = uuid4()
        request = AnalysisRequestCreate(
            idempotency_key=uuid4(),
            document_ids=[document_id],
            notice_version="notice-1",
            consent=True,
        )

        self.assertEqual(request.document_ids, [document_id])
        with self.assertRaises(ValidationError):
            AnalysisRequestCreate(
                idempotency_key=uuid4(),
                document_ids=[document_id],
                notice_version="notice-1",
                consent=False,
            )
        with self.assertRaises(ValidationError):
            AnalysisRequestCreate(
                idempotency_key=uuid4(),
                document_ids=[document_id, document_id],
                notice_version="notice-1",
                consent=True,
            )

    def test_request_status_reflects_work_and_mixed_terminal_outcomes(self) -> None:
        self.assertEqual(aggregate_analysis_status(["queued", "completed"]), "queued")
        self.assertEqual(aggregate_analysis_status(["processing", "queued"]), "processing")
        self.assertEqual(aggregate_analysis_status(["completed", "completed"]), "completed")
        self.assertEqual(aggregate_analysis_status(["failed", "failed"]), "failed")
        self.assertEqual(aggregate_analysis_status(["cancelled", "cancelled"]), "cancelled")
        self.assertEqual(aggregate_analysis_status(["completed", "partial"]), "partial")
        self.assertEqual(aggregate_analysis_status(["completed", "failed"]), "partial")


def enabled_settings() -> Settings:
    return Settings(
        auth_enabled=True,
        auth_jwt_secret="secure-test-analysis-signing-key-that-is-long-enough",
        case_data_enabled=True,
        case_materials_enabled=True,
        s3_endpoint_url="http://localhost:5000",
        ai_analysis_enabled=True,
        bedrock_model_id="test-model",
        bedrock_region="us-west-2",
        ai_analysis_notice_version="notice-1",
        ai_analysis_data_handling_notice="Deployment retention notice.",
    )


if __name__ == "__main__":
    unittest.main()
