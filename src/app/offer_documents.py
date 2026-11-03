from datetime import date, datetime
from io import BytesIO
import re

from docx import Document
from docx.shared import Inches, Pt
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.settlement_planning import SettlementScenarioResult


class MediationOfferTerms(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offer_from: str = Field(min_length=1, max_length=160)
    offer_to: str = Field(min_length=1, max_length=160)
    effective_date: date | None = None
    response_by_date: date | None = None
    terms: list[str] = Field(min_length=1, max_length=25)

    @field_validator("offer_from", "offer_to")
    @classmethod
    def party_names_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Party names cannot be blank.")
        return normalized

    @field_validator("terms")
    @classmethod
    def terms_must_not_be_blank(cls, values: list[str]) -> list[str]:
        normalized = [term.strip() for term in values]
        if any(not term for term in normalized):
            raise ValueError("Offer terms cannot be blank.")
        return normalized

    @model_validator(mode="before")
    @classmethod
    def dates_must_be_calendar_dates(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        for field in ("effective_date", "response_by_date"):
            raw_date = value.get(field)
            if isinstance(raw_date, datetime):
                raise ValueError("Use an ISO calendar date in YYYY-MM-DD format.")
            if isinstance(raw_date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_date) is None:
                raise ValueError("Use ISO calendar dates in YYYY-MM-DD format.")
        return value

    @model_validator(mode="after")
    def validate_response_date(self) -> "MediationOfferTerms":
        if (
            self.effective_date is not None
            and self.response_by_date is not None
            and self.response_by_date < self.effective_date
        ):
            raise ValueError("Response date must not be before the effective date.")
        return self


def _currency(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def render_mediation_offer_docx(
    terms: MediationOfferTerms,
    result: SettlementScenarioResult,
) -> bytes:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(10)

    heading = document.add_heading("Settlement Proposal", level=0)
    heading.paragraph_format.space_after = Pt(4)
    notice = document.add_paragraph()
    notice_run = notice.add_run("NONBINDING DRAFT — REVIEW BEFORE SHARING")
    notice_run.bold = True
    notice_run.font.size = Pt(12)
    document.add_paragraph(
        "This editable proposal is for settlement discussion only. It is not a court filing, "
        "legal advice, or a prediction of a court result. No party is bound unless all "
        "applicable requirements are satisfied."
    )

    document.add_heading("Parties and dates", level=1)
    document.add_paragraph(f"From: {terms.offer_from}")
    document.add_paragraph(f"To: {terms.offer_to}")
    if terms.effective_date is not None:
        document.add_paragraph(f"Proposed effective date: {terms.effective_date.isoformat()}")
    if terms.response_by_date is not None:
        document.add_paragraph(f"Proposed response date: {terms.response_by_date.isoformat()}")

    document.add_heading("Proposed terms", level=1)
    for term in terms.terms:
        document.add_paragraph(term, style="List Number")

    document.add_heading("Illustrative property schedule", level=1)
    document.add_paragraph(
        "Amounts below are derived from the selected scenario's stated assumptions and "
        "user-provided ledger. They are proposals, not legal classifications or valuations."
    )
    document.add_paragraph(
        "Debt ledger balances are shown as positive liability amounts and are subtracted "
        "when calculating each party's illustrative net."
    )
    table = document.add_table(rows=1, cols=6)
    table.style = "Light Shading Accent 1"
    for cell, label in zip(
        table.rows[0].cells,
        (
            "Item",
            "Type",
            "User separate",
            "Other party separate",
            "Community",
            "Unresolved",
        ),
        strict=True,
    ):
        cell.text = label
    for ledger in result.ledgers:
        cells = table.add_row().cells
        cells[0].text = ledger.name
        cells[1].text = ledger.kind.title()
        cells[2].text = _currency(ledger.balances.user_separate_cents)
        cells[3].text = _currency(ledger.balances.other_separate_cents)
        cells[4].text = _currency(ledger.balances.community_cents)
        cells[5].text = _currency(ledger.balances.unresolved_cents)

    document.add_paragraph(
        f"Illustrative net allocated to the user/offeror ({terms.offer_from}): "
        f"{_currency(result.user_net_cents)}"
    )
    document.add_paragraph(
        f"Illustrative net allocated to the other party ({terms.offer_to}): "
        f"{_currency(result.other_net_cents)}"
    )
    document.add_paragraph(
        f"Net amount still unresolved: {_currency(result.unresolved_cents)}"
    )
    document.add_heading("Scenario assumptions", level=1)
    document.add_paragraph(
        f"{result.scenario.relationship_window.label}: "
        f"{result.scenario.relationship_window.start_date.isoformat()} through "
        f"{result.scenario.relationship_window.separation_date.isoformat()}."
    )
    document.add_paragraph(f"Tracing convention used: {result.scenario.tracing_method}.")
    document.add_paragraph(
        "User-proposed community allocation: "
        f"{result.scenario.community_share_bps / 100:.2f}% to the offering party."
    )
    document.add_paragraph(
        "Have a Washington family-law attorney or mediator review the assumptions and "
        "terms before signing or sharing. This generated draft is not sent or filed."
    )

    output = BytesIO()
    document.save(output)
    return output.getvalue()
