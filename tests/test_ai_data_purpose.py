import logging
import unittest

from app.ai import analyze_document_pages
from app.config import Settings, provider_data_handling_notice
from app.failure_logging import log_failure_event


class FakeBedrockClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text

    def converse(self, **request: object) -> dict:
        return {
            "output": {
                "message": {
                    "content": [{"text": self.response_text}],
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
        bedrock_model_id="test-model",
        bedrock_region="us-west-2",
        ai_analysis_notice_version="notice-1",
        ai_analysis_data_handling_notice="Deployment handling notice.",
    )


class AIDataPurposeTests(unittest.TestCase):
    def test_ai_provider_response_and_case_content_are_not_written_to_logs(self) -> None:
        case_secret = "CASE_CONTENT_SENTINEL_923741"
        client = FakeBedrockClient(f"not JSON: {case_secret}")
        logger = logging.getLogger("app.ai")

        with self.assertLogs(logger, level=logging.WARNING) as captured:
            with self.assertRaises(ValueError):
                analyze_document_pages(
                    "opaque-document-id",
                    {1: case_secret},
                    enabled_settings(),
                    client,
                    consent_granted=True,
                )

        log_output = "\n".join(captured.output)
        self.assertNotIn(case_secret, log_output)
        self.assertIn("Bedrock returned non-JSON case analysis output.", log_output)

    def test_failure_event_log_omits_sensitive_exception_message(self) -> None:
        case_secret = "CASE_CONTENT_SENTINEL_174205"
        logger = logging.getLogger("test.ai.failure")

        with self.assertLogs(logger, level=logging.ERROR) as captured:
            log_failure_event(logger, "analysis_job_failed", ValueError(case_secret))

        log_output = "\n".join(captured.output)
        self.assertNotIn(case_secret, log_output)
        self.assertIn("error_type=ValueError", log_output)

    def test_consent_snapshot_includes_unverified_provider_caveat(self) -> None:
        notice = provider_data_handling_notice("Deployment handling notice.")
        self.assertIn("generalized model training", notice)


if __name__ == "__main__":
    unittest.main()
