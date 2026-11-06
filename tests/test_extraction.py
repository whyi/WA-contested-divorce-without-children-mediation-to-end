import hashlib
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from botocore.exceptions import BotoCoreError
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.extraction import (
    ExtractionLease,
    claim_next_extraction_job,
    enqueue_extraction_jobs,
    process_extraction_job,
    retry_failed_extraction_job,
)
from app.main import document_extraction_status
from app.models import DocumentExtraction, DocumentExtractionJob

from test_documents import create_pdf


class ExtractionQueueTests(unittest.TestCase):
    def test_enqueue_returns_existing_job_for_repeated_request(self) -> None:
        document_id = uuid4()
        request_id = uuid4()
        document = Mock(id=document_id, sha256="a" * 64)
        existing_job = Mock(status="queued")
        db = Mock()
        db.get.return_value = document
        db.scalar.return_value = existing_job

        jobs = enqueue_extraction_jobs(db, [document_id], request_id)

        self.assertEqual(jobs, [existing_job])
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_concurrent_enqueue_recovers_the_existing_unique_job(self) -> None:
        document_id = uuid4()
        document = Mock(id=document_id, sha256="f" * 64)
        existing_job = Mock(status="queued")
        db = Mock()
        db.get.return_value = document
        db.scalar.side_effect = [None, existing_job]
        db.commit.side_effect = IntegrityError("insert", {}, RuntimeError("duplicate"))

        jobs = enqueue_extraction_jobs(db, [document_id], uuid4())

        self.assertEqual(jobs, [existing_job])
        db.rollback.assert_called_once()

    def test_enqueue_persists_a_queued_job_without_processing_it(self) -> None:
        document_id = uuid4()
        request_id = uuid4()
        document = Mock(id=document_id, sha256="b" * 64)
        db = Mock()
        db.get.return_value = document
        db.scalar.return_value = None

        jobs = enqueue_extraction_jobs(db, [document_id], request_id)

        self.assertEqual(len(jobs), 1)
        self.assertIsInstance(jobs[0], DocumentExtractionJob)
        self.assertEqual(jobs[0].status, "queued")
        self.assertEqual(jobs[0].request_id, request_id)
        db.add.assert_called_once_with(jobs[0])
        db.commit.assert_called_once()

    def test_claim_uses_skip_locked_and_reclaims_expired_work(self) -> None:
        case_id = uuid4()
        case = Mock(id=case_id)
        job = Mock(
            id=uuid4(),
            status="processing",
            attempts=1,
            lease_token=None,
            lease_expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        db = Mock()
        db.scalar.side_effect = [case_id, case, 0, job]
        db.scalars.return_value.all.return_value = []

        lease = claim_next_extraction_job(db)

        self.assertIsNotNone(lease)
        self.assertEqual(job.status, "processing")
        self.assertEqual(job.attempts, 2)
        self.assertEqual(job.lease_token, lease.token)
        self.assertIsNotNone(job.lease_expires_at)
        self.assertTrue(db.scalar.call_args_list[1].args[0]._for_update_arg.skip_locked)
        db.commit.assert_called_once()

    def test_expired_job_at_attempt_limit_is_marked_failed(self) -> None:
        job = Mock(
            id=uuid4(),
            status="processing",
            attempts=4,
            error_code=None,
            lease_token=uuid4(),
            lease_expires_at=datetime.now(UTC) - timedelta(minutes=1),
            completed_at=None,
        )
        db = Mock()
        db.scalars.return_value.all.return_value = [job]
        db.scalar.return_value = None

        lease = claim_next_extraction_job(db)

        self.assertIsNone(lease)
        self.assertEqual(job.status, "failed")
        self.assertEqual(job.error_code, "worker_interrupted")
        self.assertIsNone(job.lease_token)
        db.commit.assert_called_once()

    def test_case_at_concurrency_limit_does_not_claim_another_job(self) -> None:
        case_id = uuid4()
        db = Mock()
        db.scalar.side_effect = [case_id, case_id, 3, None]
        db.scalars.return_value.all.return_value = []

        lease = claim_next_extraction_job(db)

        self.assertIsNone(lease)
        self.assertEqual(db.scalar.call_count, 4)
        db.commit.assert_any_call()

    def test_successful_processing_persists_page_provenance(self) -> None:
        content = create_pdf(["First page", "Second page"])
        document_id = uuid4()
        token = uuid4()
        job = Mock(
            id=uuid4(),
            document_id=document_id,
            source_sha256=hashlib.sha256(content).hexdigest(),
            status="processing",
            lease_token=token,
            lease_expires_at=None,
            error_code=None,
            completed_at=None,
        )
        document = Mock(
            id=document_id,
            sha256=job.source_sha256,
            object_key="opaque/document.pdf",
            extension="pdf",
        )
        db = Mock()
        db.get.side_effect = [job, document]
        db.scalar.return_value = None
        storage = Mock()
        storage.get.return_value = content

        process_extraction_job(db, storage, ExtractionLease(job.id, token))

        self.assertEqual(job.status, "completed")
        self.assertEqual(job.error_code, None)
        extraction = next(
            call.args[0]
            for call in db.add.call_args_list
            if isinstance(call.args[0], DocumentExtraction)
        )
        self.assertEqual(
            extraction.pages_json,
            [
                {"page_number": 1, "text": "First page"},
                {"page_number": 2, "text": "Second page"},
            ],
        )
        self.assertEqual(extraction.page_count, 2)
        db.commit.assert_called_once()

    def test_ocr_needed_file_is_persisted_as_needs_attention(self) -> None:
        job, _, storage, db, lease = self._processing_fixture(
            create_pdf(["Selectable text", ""])
        )

        process_extraction_job(db, storage, lease)

        self.assertEqual(job.status, "needs_attention")
        self.assertEqual(job.error_code, "ocr_required")
        self.assertEqual(db.commit.call_count, 1)

    def test_over_page_limit_pdf_needs_attention_without_saving_text(self) -> None:
        job, _, storage, db, lease = self._processing_fixture(
            create_pdf(["page"] * 201)
        )

        process_extraction_job(db, storage, lease)

        self.assertEqual(job.status, "needs_attention")
        self.assertEqual(job.error_code, "page_limit_exceeded")
        db.add.assert_not_called()

    def test_password_protected_pdf_is_persisted_as_needs_attention(self) -> None:
        job, _, storage, db, lease = self._processing_fixture(
            create_pdf(["Private page"], "secret")
        )

        process_extraction_job(db, storage, lease)

        self.assertEqual(job.status, "needs_attention")
        self.assertEqual(job.error_code, "password_protected")

    def test_storage_failure_is_reported_without_exposing_storage_details(self) -> None:
        job, _, storage, db, lease = self._processing_fixture(b"not used")
        storage.get.side_effect = BotoCoreError()

        process_extraction_job(db, storage, lease)

        self.assertEqual(job.status, "failed")
        self.assertEqual(job.error_code, "storage_unavailable")
        db.commit.assert_called_once()

    def test_retry_resets_only_failed_jobs_for_the_same_request(self) -> None:
        request_id = uuid4()
        job = Mock(
            status="failed",
            request_id=request_id,
            attempts=3,
            error_code="storage_unavailable",
            lease_token=uuid4(),
            lease_expires_at=object(),
        )
        db = Mock()
        db.scalar.return_value = job

        retried = retry_failed_extraction_job(db, job.id, request_id)

        self.assertIs(retried, job)
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.attempts, 3)
        self.assertIsNone(job.error_code)
        self.assertIsNone(job.lease_token)
        self.assertIsNone(job.lease_expires_at)
        db.commit.assert_called_once()

    def test_retry_does_not_exceed_three_retries_after_initial_attempt(self) -> None:
        job = Mock(status="failed", request_id=uuid4(), attempts=4)
        db = Mock()
        db.scalar.return_value = job

        retried = retry_failed_extraction_job(db, job.id, job.request_id)

        self.assertIs(retried, job)
        self.assertEqual(job.status, "failed")
        self.assertEqual(job.attempts, 4)
        db.commit.assert_not_called()

    def test_retry_does_not_repeat_completed_extraction(self) -> None:
        job = Mock(status="completed", request_id=uuid4())
        db = Mock()
        db.scalar.return_value = job

        result = retry_failed_extraction_job(db, job.id, job.request_id)

        self.assertIs(result, job)
        db.commit.assert_not_called()

    def test_status_is_stored_until_a_consent_request_enqueues_work(self) -> None:
        case_id = uuid4()
        document_id = uuid4()
        document = SimpleNamespace(
            id=document_id,
            case_id=case_id,
            sha256="d" * 64,
        )
        db = Mock()
        db.get.return_value = document
        db.scalar.side_effect = [None, None]

        status = document_extraction_status(case_id, document_id, db)

        self.assertEqual(status.status, "stored")
        self.assertIsNone(status.job_id)
        self.assertIsNone(status.page_count)

    def test_status_does_not_disclose_a_document_from_another_case(self) -> None:
        document = SimpleNamespace(id=uuid4(), case_id=uuid4(), sha256="e" * 64)
        db = Mock()
        db.get.return_value = document

        with self.assertRaises(HTTPException) as raised:
            document_extraction_status(uuid4(), document.id, db)

        self.assertEqual(raised.exception.status_code, 404)
        db.scalar.assert_not_called()

    def _processing_fixture(self, content: bytes):
        source_digest = hashlib.sha256(content).hexdigest()
        job = Mock(
            id=uuid4(),
            document_id=uuid4(),
            source_sha256=source_digest,
            status="processing",
            lease_token=uuid4(),
            lease_expires_at=None,
            error_code=None,
            completed_at=None,
        )
        document = Mock(
            id=job.document_id,
            sha256=source_digest,
            object_key="opaque/document.pdf",
            extension="pdf",
        )
        db = Mock()
        db.get.side_effect = [job, document]
        db.scalar.return_value = None
        storage = Mock()
        storage.get.return_value = content
        lease = ExtractionLease(job.id, job.lease_token)
        return job, document, storage, db, lease


if __name__ == "__main__":
    unittest.main()
