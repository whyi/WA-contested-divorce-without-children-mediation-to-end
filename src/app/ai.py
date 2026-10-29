import json
import logging
from collections.abc import Mapping
from typing import Literal, Protocol

import boto3
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Extract candidate case facts from the supplied documents.
Return only a JSON array. Each item must contain field_key, value,
source_document, source_quote, confidence (high, medium, or low), and
uncertainty. Use an exact quote from the named source document. Do not infer
missing facts, resolve conflicts, state legal conclusions, or recommend an
offer. An empty array is appropriate when no supported fact can be extracted."""


class BedrockConverseClient(Protocol):
    def converse(self, **request: object) -> Mapping[str, object]: ...


class ProposedField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_key: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1)
    source_document: str = Field(min_length=1)
    source_quote: str = Field(min_length=1)
    confidence: Literal["high", "medium", "low"]
    uncertainty: str


def analyze_case_materials(
    document_texts: Mapping[str, str],
    settings: Settings | None = None,
    client: BedrockConverseClient | None = None,
) -> list[ProposedField]:
    settings = settings or get_settings()
    model_id = settings.bedrock_model_id
    if not model_id or not model_id.strip():
        raise RuntimeError("BEDROCK_MODEL_ID must be configured before AI extraction is available.")
    if not document_texts or any(
        not name.strip() or not text.strip() for name, text in document_texts.items()
    ):
        raise ValueError("At least one named document with extracted text is required.")
    client = client or boto3.client(
        "bedrock-runtime",
        region_name=settings.bedrock_region or settings.s3_region,
    )

    response = client.converse(
        modelId=model_id,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[
            {
                "role": "user",
                "content": [{"text": json.dumps(document_texts, ensure_ascii=False)}],
            }
        ],
        inferenceConfig={"temperature": 0.0},
    )
    model_text = _response_text(response)
    try:
        payload = json.loads(model_text)
    except json.JSONDecodeError as error:
        logger.warning("Bedrock returned non-JSON case extraction output.")
        raise ValueError("The AI extraction response was not valid JSON.") from error

    try:
        fields = TypeAdapter(list[ProposedField]).validate_python(payload)
    except ValidationError as error:
        logger.warning("Bedrock returned case extraction output with an invalid schema.")
        raise ValueError("The AI extraction response did not match the required schema.") from error

    for field in fields:
        source_text = document_texts.get(field.source_document)
        if source_text is None or field.source_quote not in source_text:
            raise ValueError(
                f"The AI extraction source quote could not be verified for field {field.field_key!r}."
            )
    return fields


def _response_text(response: Mapping[str, object]) -> str:
    output = response.get("output")
    if not isinstance(output, Mapping):
        raise RuntimeError("Bedrock returned a response without an output message.")
    message = output.get("message")
    if not isinstance(message, Mapping):
        raise RuntimeError("Bedrock returned a response without a message.")
    content = message.get("content")
    if not isinstance(content, list) or not content:
        raise RuntimeError("Bedrock returned a response without text content.")
    first_content = content[0]
    if not isinstance(first_content, Mapping):
        raise RuntimeError("Bedrock returned an invalid content block.")
    text = first_content.get("text")
    if not isinstance(text, str):
        raise RuntimeError("Bedrock returned a response without text content.")
    return text
