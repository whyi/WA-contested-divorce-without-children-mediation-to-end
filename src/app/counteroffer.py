from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

# The product only prepares documents for the user to hand to the mediator. It never
# transmits to the opposing party and cannot observe delivery or the mediator's reply.
DELIVERY_BOUNDARY = {
    "recipient": "mediator",
    "sent_to_opposing_party": False,
    "delivery_verified_by_app": False,
    "response_verified_by_app": False,
    "basis": "user_reported",
}


class CounterofferValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID
    amount_cents: int = Field(ge=-1_000_000_000_000, le=1_000_000_000_000)


class CounterofferValuesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_attempt_revision: int = Field(ge=0)
    source: Literal["mediator_reported", "document_reviewed"]
    values: list[CounterofferValue] = Field(default_factory=list, max_length=500)
    note: str = Field(default="", max_length=1_000)
    reviewed: bool = True

    @model_validator(mode="after")
    def validate_values(self) -> "CounterofferValuesUpdate":
        ids = [value.asset_id for value in self.values]
        if len(ids) != len(set(ids)):
            raise ValueError("Each asset may appear only once.")
        if self.source == "document_reviewed" and not self.reviewed:
            raise ValueError("Document-derived values must be reviewed before they are recorded.")
        return self


def build_counteroffer_record(
    payload: CounterofferValuesUpdate, known_asset_ids: set[str], now: datetime
) -> dict:
    if any(str(value.asset_id) not in known_asset_ids for value in payload.values):
        raise HTTPException(
            status_code=422,
            detail="Counteroffer values must reference an asset in this attempt snapshot.",
        )
    return {
        "source": payload.source,
        "values": [
            {"asset_id": str(value.asset_id), "amount_cents": value.amount_cents}
            for value in payload.values
        ],
        "note": payload.note.strip(),
        "recorded_at": now.isoformat(),
        "verified_by_app": False,
    }


def prior_attempt_context(predecessor: object, outcome: str | None, counteroffer: dict | None) -> dict:
    """Read-only view of the earlier round; the user's and the counteroffer's values stay separate."""
    state = getattr(predecessor, "editable_state_json", None) or {}
    return {
        "attempt_ordinal": predecessor.attempt_ordinal,
        "outcome": outcome,
        "user_proposed_values": list(state.get("proposed_values", [])),
        "counteroffer": counteroffer,
    }


def suggest_counteroffer_values(extension: str, content: bytes, known_assets: list[dict]) -> dict:
    """Optional analysis of a received document. Output is a suggestion only, never a recorded offer."""
    from app.modified_offer import ModifiedOfferParseError, _parse_xlsx

    result = {"source": "document_analysis", "adopted": False, "suggestions": [], "warnings": []}
    if extension != "xlsx":
        result["warnings"].append(
            "Automatic analysis is available for XLSX files only. Enter the values manually."
        )
        return result
    try:
        _, values, warnings = _parse_xlsx(content, known_assets)
    except ModifiedOfferParseError as error:
        result["warnings"].append(f"{error} Enter the values manually.")
        return result
    result["suggestions"] = [
        {"asset_id": item["asset_id"], "amount_cents": item["proposed_amount_cents"]}
        for item in values
    ]
    result["warnings"] = warnings
    if not values:
        result["warnings"].append("No values were recognized. Enter the values manually.")
    return result
