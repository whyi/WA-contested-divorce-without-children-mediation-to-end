import json
import unittest

from app.ai import analyze_case_materials
from app.config import Settings


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
            Settings(bedrock_model_id="test-model"),
            client,
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
                Settings(bedrock_model_id="test-model"),
                client,
            )

    def test_surfaces_invalid_model_output(self) -> None:
        client = FakeBedrockClient(bedrock_response("not json"))

        with self.assertRaisesRegex(ValueError, "valid JSON"):
            analyze_case_materials(
                {"case.pdf": "Case facts"},
                Settings(bedrock_model_id="test-model"),
                client,
            )

    def test_requires_a_configured_model(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "BEDROCK_MODEL_ID"):
            analyze_case_materials({"case.pdf": "Case facts"}, Settings())


if __name__ == "__main__":
    unittest.main()
