from datetime import date, datetime
from io import BytesIO
import re

from docx import Document
from docx.shared import Inches, Pt
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.settlement_planning import SettlementScenarioResult


def _validate_xml_text(value: str) -> str:
    if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
        raise ValueError("Text contains unsupported control characters.")
    return value


class MediationOfferTerms(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offer_from: str = Field(min_length=1, max_length=160)
    offer_to: str = Field(min_length=1, max_length=160)
    county: str | None = Field(default=None, max_length=100)
    court_case_number: str | None = Field(default=None, max_length=100)
    effective_date: date | None = None
    response_by_date: date | None = None
    terms: list[str] = Field(min_length=1, max_length=25)

    @field_validator("offer_from", "offer_to")
    @classmethod
    def party_names_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Party names cannot be blank.")
        return _validate_xml_text(normalized)

    @field_validator("county", "court_case_number")
    @classmethod
    def optional_caption_fields_must_not_be_blank(cls, value: str | None) -> str | None:
        normalized = value.strip() if value is not None else None
        if normalized == "":
            return None
        return _validate_xml_text(normalized) if normalized is not None else None

    @field_validator("terms")
    @classmethod
    def terms_must_not_be_blank(cls, values: list[str]) -> list[str]:
        normalized = [term.strip() for term in values]
        if any(not term for term in normalized):
            raise ValueError("Offer terms cannot be blank.")
        if any(len(term) > 2_000 for term in normalized):
            raise ValueError("Each offer term must be 2,000 characters or fewer.")
        for term in normalized:
            _validate_xml_text(term)
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

    heading = document.add_heading("CR 2A AGREEMENT — PROPOSED DRAFT", level=0)
    heading.paragraph_format.space_after = Pt(4)
    notice = document.add_paragraph()
    notice_run = notice.add_run("UNSIGNED DRAFT — REVIEW BEFORE SIGNING OR SHARING")
    notice_run.bold = True
    notice_run.font.size = Pt(12)
    document.add_paragraph(
        "This editable CR 2A-style proposal is not signed, filed, or legal advice. A signed "
        "agreement may have legal effect. Review the terms and form with qualified Washington "
        "family-law counsel before signing or sharing."
    )

    document.add_heading("Superior Court of Washington", level=1)
    document.add_paragraph(f"County: {terms.county or '____________________________'}")
    document.add_paragraph(
        f"Cause number: {terms.court_case_number or '____________________________'}"
    )
    document.add_paragraph(
        f"Petitioner / proposing party: {terms.offer_from}"
    )
    document.add_paragraph(f"Respondent / receiving party: {terms.offer_to}")
    document.add_heading("Agreement terms proposed for review", level=1)
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
        "The parties should review and complete any required provisions, dates, and signatures "
        "with qualified Washington family-law counsel. This generated draft is not signed, "
        "sent, or filed."
    )
    document.add_heading("Signatures", level=1)
    document.add_paragraph(
        f"{terms.offer_from}: ____________________________________    Date: ______________"
    )
    document.add_paragraph(
        f"{terms.offer_to}: ______________________________________    Date: ______________"
    )
    document.add_paragraph(
        "Attorney approval, if applicable: _______________________    Date: ______________"
    )

    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _set_safe_text(cell, value: str) -> None:
    cell.value = value
    cell.data_type = "s"


def render_property_schedule_xlsx(
    terms: MediationOfferTerms,
    result: SettlementScenarioResult,
) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Property Division"
    assumptions = workbook.create_sheet("Scenario Assumptions")
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True

    sheet.merge_cells("A1:I1")
    _set_safe_text(sheet["A1"], "CR 2A Property-Division Proposal — Draft")
    sheet["A1"].font = Font(bold=True, size=16, color="FFFFFF")
    sheet["A1"].fill = PatternFill("solid", fgColor="355C49")
    sheet["A1"].alignment = Alignment(vertical="center")
    sheet.row_dimensions[1].height = 26
    sheet.merge_cells("A2:I2")
    _set_safe_text(
        sheet["A2"],
        "Unsigned draft for review. Amounts and allocations are proposals, not legal conclusions or valuations.",
    )
    sheet["A2"].alignment = Alignment(wrap_text=True)
    sheet.merge_cells("A3:I3")
    _set_safe_text(sheet["A3"], f"Proposing party: {terms.offer_from}    Other party: {terms.offer_to}")

    headers = (
        "Property or debt",
        "Type",
        "User separate",
        "Other party separate",
        "Community",
        "Unresolved",
        "Total",
        "Proposed to user",
        "Proposed to other party",
    )
    header_row = 5
    for column, label in enumerate(headers, 1):
        cell = sheet.cell(header_row, column)
        _set_safe_text(cell, label)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="527764")
        cell.alignment = Alignment(wrap_text=True, vertical="center")

    first_data_row = header_row + 1
    share = result.scenario.community_share_bps / 10_000
    for row_number, ledger in enumerate(result.ledgers, first_data_row):
        _set_safe_text(sheet.cell(row_number, 1), ledger.name)
        _set_safe_text(sheet.cell(row_number, 2), ledger.kind.title())
        for column, cents in enumerate(
            (
                ledger.balances.user_separate_cents,
                ledger.balances.other_separate_cents,
                ledger.balances.community_cents,
                ledger.balances.unresolved_cents,
            ),
            3,
        ):
            sheet.cell(row_number, column, cents / 100)
        sheet.cell(row_number, 7, f"=SUM(C{row_number}:F{row_number})")
        sheet.cell(row_number, 8, f"=C{row_number}+E{row_number}*'Scenario Assumptions'!$B$6")
        sheet.cell(row_number, 9, f"=D{row_number}+E{row_number}*(1-'Scenario Assumptions'!$B$6)")

    last_data_row = max(first_data_row, first_data_row + len(result.ledgers) - 1)
    total_row = last_data_row + 1
    _set_safe_text(sheet.cell(total_row, 1), "Total")
    for column in range(3, 10):
        letter = get_column_letter(column)
        sheet.cell(total_row, column, f"=SUM({letter}{first_data_row}:{letter}{last_data_row})")
    sheet.cell(total_row + 1, 1, "Net to user (assets less debts)")
    sheet.cell(
        total_row + 1,
        8,
        f"=SUMIF(B{first_data_row}:B{last_data_row},\"Asset\",H{first_data_row}:H{last_data_row})-SUMIF(B{first_data_row}:B{last_data_row},\"Debt\",H{first_data_row}:H{last_data_row})",
    )
    sheet.cell(total_row + 2, 1, "Net to other party (assets less debts)")
    sheet.cell(
        total_row + 2,
        9,
        f"=SUMIF(B{first_data_row}:B{last_data_row},\"Asset\",I{first_data_row}:I{last_data_row})-SUMIF(B{first_data_row}:B{last_data_row},\"Debt\",I{first_data_row}:I{last_data_row})",
    )
    sheet.cell(total_row + 3, 1, "Net unresolved (assets less debts)")
    sheet.cell(
        total_row + 3,
        6,
        f'=SUMIF(B{first_data_row}:B{last_data_row},"Asset",F{first_data_row}:F{last_data_row})'
        f'-SUMIF(B{first_data_row}:B{last_data_row},"Debt",F{first_data_row}:F{last_data_row})',
    )

    for row in sheet.iter_rows(
        min_row=first_data_row,
        max_row=total_row + 3,
        min_col=3,
        max_col=9,
    ):
        for cell in row:
            cell.number_format = '$#,##0.00;[Red]($#,##0.00)'
    for cell in sheet[total_row]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="E7EFE9")
    sheet.freeze_panes = f"A{first_data_row}"
    sheet.auto_filter.ref = f"A{header_row}:I{last_data_row}"
    sheet.row_dimensions[header_row].height = 34
    for column, width in enumerate((34, 14, 17, 20, 17, 17, 17, 19, 22), 1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    for row in sheet.iter_rows(min_row=1, max_row=total_row + 3):
        for cell in row:
            cell.alignment = Alignment(
                horizontal=cell.alignment.horizontal,
                vertical="top",
                wrap_text=True,
            )

    assumption_values = (
        ("Scenario assumption", "Selected value"),
        ("Scenario", result.scenario.relationship_window.label),
        ("Relationship start", result.scenario.relationship_window.start_date.isoformat()),
        ("Separation date", result.scenario.relationship_window.separation_date.isoformat()),
        ("Tracing convention", result.scenario.tracing_method),
        ("Community share fraction", share),
        ("Offering party", terms.offer_from),
        ("Other party", terms.offer_to),
        ("Scenario ID", result.scenario.id),
    )
    for row_number, (label, value) in enumerate(assumption_values, 1):
        _set_safe_text(assumptions.cell(row_number, 1), label)
        if isinstance(value, str):
            _set_safe_text(assumptions.cell(row_number, 2), value)
        else:
            assumptions.cell(row_number, 2, value)
    assumptions["A1"].font = Font(bold=True, color="FFFFFF")
    assumptions["B1"].font = Font(bold=True, color="FFFFFF")
    assumptions["A1"].fill = PatternFill("solid", fgColor="527764")
    assumptions["B1"].fill = PatternFill("solid", fgColor="527764")
    assumptions["B6"].number_format = "0.00%"
    assumptions.column_dimensions["A"].width = 38
    assumptions.column_dimensions["B"].width = 56
    assumptions.freeze_panes = "A2"

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
