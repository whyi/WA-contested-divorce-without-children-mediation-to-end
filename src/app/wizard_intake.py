import logging
from datetime import date as Date
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.case_lifecycle import lifecycle_write_allowed
from app.database import get_db
from app.failure_logging import log_failure_event
from app.models import Case, User
from app.property_tracing import validate_iso_calendar_date
from app.settlement_routes import _authorize_case, _lock_case

logger = logging.getLogger(__name__)
router = APIRouter(tags=["wizard intake"])
WizardEntry = TypeVar("WizardEntry", bound=BaseModel)


class WizardIntakeDate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: Date | None = None
    unknown: bool = False

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: object) -> object:
        return validate_iso_calendar_date(value)

    @model_validator(mode="after")
    def unknown_date_must_be_empty(self) -> "WizardIntakeDate":
        if self.unknown and self.date is not None:
            raise ValueError("A date cannot be both entered and marked unknown.")
        return self


class WizardIntakeDates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohabitation: WizardIntakeDate = Field(default_factory=WizardIntakeDate)
    marriage: WizardIntakeDate = Field(default_factory=WizardIntakeDate)
    separation: WizardIntakeDate = Field(default_factory=WizardIntakeDate)
    petition: WizardIntakeDate = Field(default_factory=WizardIntakeDate)


class WizardFinanceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    kind: Literal["asset", "debt"] = "asset"
    category: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=1000)
    acquired_date: Date | None = None
    acquisition_method: Literal[
        "purchase", "inheritance", "gift", "pre_existing", "other"
    ] | None = None
    amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    owners: str = Field(default="", max_length=240)
    holding: Literal["individual", "joint", "unclear"] | None = None

    @field_validator("acquired_date", mode="before")
    @classmethod
    def validate_acquired_date(cls, value: object) -> object:
        return validate_iso_calendar_date(value)

    @field_validator("amount", mode="before")
    @classmethod
    def empty_amount_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("acquisition_method", "holding", mode="before")
    @classmethod
    def empty_selection_is_none(cls, value: object) -> object:
        return None if value == "" else value


class WizardIssueEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    topic: str = Field(default="", max_length=240)
    outcome: str = Field(default="", max_length=2000)


class WizardAgreementEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    summary: str = Field(default="", max_length=2000)
    date: Date | None = None

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: object) -> object:
        return validate_iso_calendar_date(value)


def _unique_entry_ids(entries: list[WizardEntry]) -> list[WizardEntry]:
    ids = [getattr(entry, "id") for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("Wizard entry IDs must be unique within a section.")
    return entries


class WizardIntakeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    filed: Literal["yes", "no"] | None = None
    role: Literal["petitioner", "respondent"] | None = None
    dates: WizardIntakeDates = Field(default_factory=WizardIntakeDates)
    finances: list[WizardFinanceEntry] = Field(default_factory=list, max_length=250)
    issues: list[WizardIssueEntry] = Field(default_factory=list, max_length=250)
    agreements: list[WizardAgreementEntry] = Field(default_factory=list, max_length=250)

    @field_validator("finances", "issues", "agreements")
    @classmethod
    def entries_have_unique_ids(cls, value: list[WizardEntry]) -> list[WizardEntry]:
        return _unique_entry_ids(value)


class WizardIntakeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(ge=0)
    draft: WizardIntakeDraft


class WizardIntakeRead(BaseModel):
    revision: int
    draft: WizardIntakeDraft
    updated_at: datetime | None


def _read(case: Case) -> WizardIntakeRead:
    try:
        draft = WizardIntakeDraft.model_validate(case.wizard_intake_json or {})
    except ValidationError as error:
        logger.error("Stored wizard-intake draft failed schema validation.")
        raise HTTPException(
            status_code=503,
            detail="The saved wizard draft is unavailable. Please contact support.",
        ) from error
    return WizardIntakeRead(
        revision=case.wizard_intake_revision,
        draft=draft,
        updated_at=case.updated_at,
    )


@router.get(
    "/cases/{case_id}/wizard-intake",
    response_model=WizardIntakeRead,
)
def read_wizard_intake(
    case_id: UUID,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WizardIntakeRead:
    response.headers["Cache-Control"] = "no-store"
    try:
        case = _authorize_case(db, user, case_id, write=False)
        return _read(case)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        log_failure_event(logger, "wizard_intake_read_failed", error)
        raise HTTPException(
            status_code=503,
            detail="The saved wizard draft is unavailable. Please try again.",
        ) from error


@router.put(
    "/cases/{case_id}/wizard-intake",
    response_model=WizardIntakeRead,
)
def update_wizard_intake(
    case_id: UUID,
    payload: WizardIntakeUpdate,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WizardIntakeRead:
    try:
        _authorize_case(db, user, case_id, write=True)
        case = _lock_case(db, case_id)
        if not lifecycle_write_allowed(case, f"/cases/{case_id}/wizard-intake"):
            raise HTTPException(
                status_code=409,
                detail="This case is closed and read-only. Reopen it to make changes.",
            )
        if case.wizard_intake_revision != payload.expected_revision:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="This wizard draft changed elsewhere. Reload the case before saving again.",
            )
        case.wizard_intake_json = payload.draft.model_dump(mode="json")
        case.wizard_intake_revision += 1
        db.commit()
        return _read(case)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        log_failure_event(logger, "wizard_intake_write_failed", error)
        raise HTTPException(
            status_code=503,
            detail="The wizard draft could not be saved. Please try again.",
        ) from error
