import json
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.analysis_worker import (
    AnalysisLease,
    claim_next_analysis_job,
    process_analysis_job,
)
from app.config import Settings
from app.models import DocumentAnalysisProposal


class FakeBedrockClient:
    def __init__(self, proposals: list[dict]) -> None:
        self.proposals = proposals
        self.call_count = 0

    def converse(self, **request: object) -> dict:
        self.call_count += 1
        return {
            "output": {
                "message": {
                    "content": [{"text": json.dumps(self.proposals)}],
                }
            }
        }


def enabled_settings() -> Settings:
    return Settings(
        auth_enabled=True,
        auth_jwt_secret="secure-test-analysis-signing-key-that-is-long-enough",
        case_data_enabled=True,
        case_materials_enabled=True,
        s3_endpoint_url="http://localhost:5000",
        ai_analysis_enabled=True,
        ai_analysis_notice_version="notice-1",
        ai_analysis_data_handling_notice="Deployment retention notice.",
        bedrock_model_id="test-model",
        bedrock_region="us-west-2",
    )


class AnalysisWorkerTests(unittest.TestCase):
    def test_worker_claims_a_queued_job(self) -> None:
        job = SimpleNamespace(
            id=uuid4(),
            request_id=uuid4(),
            status="queued",
            attempts=0,
            lease_token=None,
            lease_expires_at=None,
            error_code=None,
        )
        request = SimpleNamespace(status="queued")
        db = Mock()
        db.scalars.return_value.all.return_value = []
        db.scalar.return_value = job
        db.get.return_value = request

        lease = claim_next_analysis_job(db)

        self.assertIsNotNone(lease)
        self.assertEqual(lease.job_id, job.id)
        self.assertEqual(job.status, "processing")
        self.assertEqual(job.attempts, 1)
        self.assertEqual(request.status, "processing")
        db.commit.assert_called_once()

    def test_worker_persists_only_a_verified_proposal(self) -> None:
        document_id = uuid4()
        request_id = uuid4()
        consent_id = uuid4()
        job = SimpleNamespace(
            id=uuid4(),
            request_id=request_id,
            document_id=document_id,
            source_sha256="a" * 64,
            status="processing",
            lease_token=uuid4(),
            attempts=1,
            error_code=None,
            lease_expires_at=None,
            completed_at=None,
        )
        request = SimpleNamespace(
            id=request_id,
            case_id=uuid4(),
            consent_id=consent_id,
            status="processing",
        )
        consent = SimpleNamespace(
            id=consent_id,
            request_id=request_id,
            case_id=request.case_id,
            user_id=uuid4(),
            revoked_at=None,
            notice_version="notice-1",
            model_id="test-model",
            region="us-west-2",
            data_handling_notice="Deployment retention notice.",
        )
        request.user_id = consent.user_id
        document = SimpleNamespace(
            id=document_id,
            case_id=request.case_id,
            sha256=job.source_sha256,
        )
        extraction_job = SimpleNamespace(
            document_id=document_id,
            source_sha256=job.source_sha256,
            status="completed",
        )
        extraction = SimpleNamespace(
            extracted_text="Income: $5,000",
            pages_json=[{"page_number": 1, "text": "Income: $5,000"}],
        )
        db = Mock()
        db.get.side_effect = [job, request, document]
        db.scalar.side_effect = [
            consent,
            SimpleNamespace(role="owner"),
            extraction_job,
            extraction,
        ]
        db.scalars.return_value.all.return_value = ["completed"]
        client = FakeBedrockClient(
            [
                {
                    "field_key": "monthly_income",
                    "value": "$5,000",
                    "source_document": str(document_id),
                    "source_page_number": 1,
                    "source_quote": "Income: $5,000",
                    "confidence": "high",
                    "uncertainty": "",
                }
            ]
        )

        process_analysis_job(
            db,
            AnalysisLease(job.id, job.lease_token),
            settings=enabled_settings(),
            client=client,
        )

        self.assertEqual(client.call_count, 1)
        self.assertEqual(job.status, "completed")
        self.assertEqual(request.status, "completed")
        proposal = next(
            call.args[0]
            for call in db.add.call_args_list
            if isinstance(call.args[0], DocumentAnalysisProposal)
        )
        self.assertEqual(proposal.document_id, document_id)
        self.assertEqual(proposal.source_page_number, 1)
        self.assertEqual(proposal.source_quote, "Income: $5,000")
        db.commit.assert_called_once()

    def test_revoked_consent_cancels_job_without_calling_bedrock(self) -> None:
        job = SimpleNamespace(
            id=uuid4(),
            request_id=uuid4(),
            status="processing",
            lease_token=uuid4(),
            lease_expires_at=None,
            error_code=None,
            completed_at=None,
        )
        request = SimpleNamespace(id=job.request_id, consent_id=uuid4(), status="processing")
        consent = SimpleNamespace(
            id=request.consent_id,
            request_id=request.id,
            case_id=uuid4(),
            user_id=uuid4(),
            revoked_at=datetime.now(),
        )
        request.case_id = consent.case_id
        request.user_id = consent.user_id
        db = Mock()
        db.get.side_effect = [job, request]
        db.scalar.return_value = consent
        db.scalars.return_value.all.return_value = ["cancelled"]
        client = FakeBedrockClient([])

        process_analysis_job(
            db,
            AnalysisLease(job.id, job.lease_token),
            settings=enabled_settings(),
            client=client,
        )

        self.assertEqual(job.status, "cancelled")
        self.assertEqual(job.error_code, "consent_revoked")
        self.assertEqual(client.call_count, 0)
        db.commit.assert_called_once()

    def test_provider_is_not_called_when_analysis_is_disabled(self) -> None:
        job = SimpleNamespace(
            id=uuid4(),
            request_id=uuid4(),
            status="processing",
            lease_token=uuid4(),
            lease_expires_at=None,
            error_code=None,
            completed_at=None,
        )
        request = SimpleNamespace(id=job.request_id, consent_id=uuid4(), status="processing")
        consent = SimpleNamespace(
            id=request.consent_id,
            request_id=request.id,
            case_id=uuid4(),
            user_id=uuid4(),
            revoked_at=None,
        )
        request.case_id = consent.case_id
        request.user_id = consent.user_id
        db = Mock()
        db.get.side_effect = [job, request]
        db.scalar.return_value = consent
        db.scalars.return_value.all.return_value = ["cancelled"]
        client = FakeBedrockClient([])

        process_analysis_job(
            db,
            AnalysisLease(job.id, job.lease_token),
            settings=Settings(),
            client=client,
        )

        self.assertEqual(job.status, "cancelled")
        self.assertEqual(job.error_code, "analysis_unavailable")
        self.assertEqual(client.call_count, 0)
        db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
