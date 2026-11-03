import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AcquisitionMethod = Literal["purchase", "inheritance", "gift", "pre_existing", "other"]
TitleStatus = Literal["joint", "individual"]
AssetClassification = Literal[
    "separate_property_candidate",
    "community_property_candidate",
    "post_separation_candidate",
    "needs_review",
]


class RelationshipMilestones(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohabitation_start_date: date | None = None
    marriage_date: date | None = None
    separation_start_date: date | None = None
    divorce_filing_date: date | None = None

    @field_validator(
        "cohabitation_start_date",
        "marriage_date",
        "separation_start_date",
        "divorce_filing_date",
        mode="before",
    )
    @classmethod
    def milestone_dates_must_be_iso_calendar_dates(cls, value: object) -> object:
        return validate_iso_calendar_date(value)


class PropertyAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    acquisition_date: date
    acquisition_method: AcquisitionMethod
    title_status: TitleStatus

    @field_validator("acquisition_date", mode="before")
    @classmethod
    def acquisition_date_must_be_iso_calendar_date(cls, value: object) -> object:
        return validate_iso_calendar_date(value)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Asset name cannot be blank.")
        return normalized


class PropertyTracingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_milestones: RelationshipMilestones
    assets: list[PropertyAsset] = Field(max_length=250)


def validate_iso_calendar_date(value: object) -> object:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        raise ValueError("Use an ISO calendar date in YYYY-MM-DD format.")
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        raise ValueError("Use an ISO calendar date in YYYY-MM-DD format.")
    return value


def classify_asset(
    asset: PropertyAsset,
    milestones: RelationshipMilestones,
) -> AssetClassification:
    if asset.acquisition_method in {"inheritance", "gift", "pre_existing"}:
        return "separate_property_candidate"

    relationship_starts = [
        milestone
        for milestone in (
            milestones.cohabitation_start_date,
            milestones.marriage_date,
        )
        if milestone is not None
    ]
    relationship_start = min(relationship_starts) if relationship_starts else None
    separation = milestones.separation_start_date

    if relationship_start is not None and asset.acquisition_date < relationship_start:
        return "separate_property_candidate"
    if separation is not None and asset.acquisition_date > separation:
        return "post_separation_candidate"
    if relationship_start is None or separation is None:
        return "needs_review"
    if (
        asset.acquisition_date <= separation
        and asset.acquisition_method == "purchase"
        and asset.title_status == "joint"
    ):
        return "community_property_candidate"
    return "needs_review"
