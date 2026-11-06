import json
import unittest

from app.ai import analyze_case_materials
from app.config import Settings


def enabled_ai_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "auth_enabled": True,
        "auth_jwt_secret": "secure-test-analysis-signing-key-that-is-long-enough",
        "case_data_enabled": True,
        "case_materials_enabled": True,
        "s3_endpoint_url": "http://localhost:5000",
        "ai_analysis_enabled": True,
        "bedrock_model_id": "test-model",
        "bedrock_region": "us-west-2",
        "ai_analysis_notice_version": "notice-1",
        "ai_analysis_data_handling_notice": "Deployment review is pending.",
    }
    values.update(overrides)
    return Settings(**values)


class FakeBedrockClient:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.request: dict | None = None

    def converse(self, **request: object) -> dict:
        self.request = request
        return self.response


def bedrock_response(content: str) -> dict:
    return {
        "output": {
            "message": {
                "content": [{"text": content}],
            }
        }
    }


class BedrockExtractionTests(unittest.TestCase):
    def test_returns_only_fields_with_verifiable_source_quotes(self) -> None:
        payload = [
            {
                "field_key": "monthly_income",
                "value": "$5,000",
                "source_document": "financial_statement.pdf",
                "source_quote": "Monthly income: $5,000",
                "confidence": "high",
                "uncertainty": "",
            }
        ]
        client = FakeBedrockClient(bedrock_response(json.dumps(payload)))

        result = analyze_case_materials(
            {"financial_statement.pdf": "Monthly income: $5,000"},
            enabled_ai_settings(),
            client,
            consent_granted=True,
        )

        self.assertEqual(result[0].field_key, "monthly_income")
        self.assertEqual(client.request["modelId"], "test-model")

    def test_rejects_unverifiable_source_quotes(self) -> None:
        payload = [
            {
                "field_key": "monthly_income",
                "value": "$50,000",
                "source_document": "financial_statement.pdf",
                "source_quote": "Monthly income: $50,000",
                "confidence": "high",
                "uncertainty": "",
            }
        ]
        client = FakeBedrockClient(bedrock_response(json.dumps(payload)))

        with self.assertRaisesRegex(ValueError, "source quote"):
            analyze_case_materials(
                {"financial_statement.pdf": "Monthly income: $5,000"},
                enabled_ai_settings(),
                client,
                consent_granted=True,
            )

    def test_surfaces_invalid_model_output(self) -> None:
        client = FakeBedrockClient(bedrock_response("not json"))

        with self.assertRaisesRegex(ValueError, "valid JSON"):
            analyze_case_materials(
                {"case.pdf": "Case facts"},
                enabled_ai_settings(),
                client,
                consent_granted=True,
            )

    def test_requires_explicit_consent_before_provider_call(self) -> None:
        client = FakeBedrockClient(bedrock_response("[]"))
        with self.assertRaisesRegex(RuntimeError, "Explicit user analysis consent"):
            analyze_case_materials(
                {"case.pdf": "Case facts"},
                enabled_ai_settings(),
                client,
            )
        self.assertIsNone(client.request)

    def test_requires_a_configured_model(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unavailable under the current configuration"):
            analyze_case_materials(
                {"case.pdf": "Case facts"},
                enabled_ai_settings(bedrock_model_id=None),
                consent_granted=True,
            )

    def test_document_analysis_verifies_page_citations_and_uses_no_tools(self) -> None:
        from app.ai import analyze_document_pages

        document_id = "42de0a14-4264-4f2b-a8c0-67c4eb4a3c4b"
        payload = [
            {
                "field_key": "monthly_income",
                "value": "$5,000",
                "source_document": document_id,
                "source_page_number": 2,
                "source_quote": "Monthly income: $5,000",
                "confidence": "high",
                "uncertainty": "",
            }
        ]
        client = FakeBedrockClient(bedrock_response(json.dumps(payload)))

        result = analyze_document_pages(
            document_id,
            {1: "Case title", 2: "Monthly income: $5,000"},
            enabled_ai_settings(),
            client,
            consent_granted=True,
        )

        self.assertEqual(len(result.proposals), 1)
        self.assertEqual(result.proposals[0].source_page_number, 2)
        self.assertEqual(result.rejected_count, 0)
        self.assertNotIn("toolConfig", client.request)
        provider_request = json.dumps(client.request)
        self.assertIn("Monthly income: $5,000", provider_request)
        self.assertNotIn("training", provider_request.lower())
        self.assertNotIn("improvement", provider_request.lower())
        self.assertNotIn("toolConfig", client.request)

    def test_document_analysis_discards_unverifiable_proposals_individually(self) -> None:
        from app.ai import analyze_document_pages

        document_id = "42de0a14-4264-4f2b-a8c0-67c4eb4a3c4b"
        payload = [
            {
                "field_key": "monthly_income",
                "value": "$5,000",
                "source_document": document_id,
                "source_page_number": 1,
                "source_quote": "Monthly income: $5,000",
                "confidence": "high",
                "uncertainty": "",
            },
            {
                "field_key": "home_value",
                "value": "$900,000",
                "source_document": document_id,
                "source_page_number": 1,
                "source_quote": "The home is worth $900,000",
                "confidence": "high",
                "uncertainty": "",
            },
        ]
        client = FakeBedrockClient(bedrock_response(json.dumps(payload)))

        result = analyze_document_pages(
            document_id,
            {1: "Monthly income: $5,000"},
            enabled_ai_settings(),
            client,
            consent_granted=True,
        )

        self.assertEqual([item.field_key for item in result.proposals], ["monthly_income"])
        self.assertEqual(result.rejected_count, 1)

    def test_docx_analysis_requires_document_level_quotes_without_fake_pages(self) -> None:
        from app.ai import analyze_document_pages

        document_id = "42de0a14-4264-4f2b-a8c0-67c4eb4a3c4b"
        payload = [
            {
                "field_key": "asset",
                "value": "Savings account",
                "source_document": document_id,
                "source_page_number": 1,
                "source_quote": "Savings account",
                "confidence": "medium",
                "uncertainty": "",
            }
        ]
        client = FakeBedrockClient(bedrock_response(json.dumps(payload)))

        result = analyze_document_pages(
            document_id,
            {None: "Savings account"},
            enabled_ai_settings(),
            client,
            consent_granted=True,
        )

        self.assertEqual(result.proposals, ())
        self.assertEqual(result.rejected_count, 1)


if __name__ == "__main__":
    unittest.main()
