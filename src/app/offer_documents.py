from datetime import date, datetime
from io import BytesIO
import re
from uuid import UUID

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils import get_column_letter
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.settlement_planning import SettlementScenarioResult


PROPOSED_DISCLOSURE_LABEL = "PROPOSED DISCLOSURE — PENDING QUALIFIED COUNSEL REVIEW"
PROPOSAL_BOUNDARY_DISCLOSURE = (
    "This file is an unsigned draft and is not filed. Casework is a preparation and "
    "organization tool, not legal advice or representation. "
    "It cannot guarantee correctness, fairness, acceptance, or any particular outcome. "
    "Review all source facts, assumptions, calculations, and proposal terms. If you choose "
    "to use this proposal, review it, download it, and provide it to your mediator. "
    "Downloading is not delivery; the product does not automatically deliver proposals. "
    "Any optional external transfer is user-initiated to a destination confirmed in the "
    "interface and is not proof of mediator receipt."
)


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
    milestones: list["ProposalMilestone"] = Field(default_factory=list, max_length=100)
    proposed_values: list["ProposalValue"] = Field(default_factory=list, max_length=500)

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


class ProposalMilestone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    date: date

    @field_validator("name")
    @classmethod
    def milestone_name_is_safe_xml_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Milestone names cannot be blank.")
        return _validate_xml_text(normalized)


class ProposalValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID
    proposed_amount_cents: int = Field(ge=-1_000_000_000_000, le=1_000_000_000_000)


MediationOfferTerms.model_rebuild()


def _currency(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def render_mediation_offer_docx(
    terms: MediationOfferTerms,
    result: SettlementScenarioResult,
) -> bytes:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    document.styles["Normal"].font.name = "Arial"
    document.styles["Normal"].font.size = Pt(10)
    document.styles["Normal"].paragraph_format.space_after = Pt(4)
    for style_name in ("Heading 1", "Heading 2"):
        document.styles[style_name].font.name = "Arial"
        document.styles[style_name].font.color.rgb = RGBColor(0, 0, 0)
    document.styles["Heading 2"].font.size = Pt(11)
    document.styles["Heading 2"].font.bold = True

    court = document.add_paragraph()
    court.alignment = WD_ALIGN_PARAGRAPH.CENTER
    court.paragraph_format.space_after = Pt(0)
    court_run = court.add_run("IN THE SUPERIOR COURT OF THE STATE OF WASHINGTON")
    court_run.bold = True
    court_run.font.size = Pt(11)
    county = document.add_paragraph()
    county.alignment = WD_ALIGN_PARAGRAPH.CENTER
    county.paragraph_format.space_after = Pt(8)
    county.add_run(f"FOR {terms.county.upper() if terms.county else '[COUNTY]'} COUNTY")

    caption = document.add_table(rows=1, cols=2)
    caption.style = "Table Grid"
    caption.autofit = False
    caption_widths = (Inches(3.35), Inches(3.15))
    for column, width in zip(caption.columns, caption_widths, strict=True):
        column.width = width
        for cell in column.cells:
            cell.width = width
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    caption.cell(0, 0).text = (
        f"In re:\nProposing party: {terms.offer_from}\n"
        f"Other party: {terms.offer_to}"
    )
    caption.cell(0, 1).text = (
        f"NO. {terms.court_case_number or '________________________'}\n"
        "CR 2A AGREEMENT"
    )
    for cell in caption.rows[0].cells:
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.space_after = Pt(2)
        if len(cell.paragraphs) > 1:
            for run in cell.paragraphs[-1].runs:
                run.bold = True
    document.add_paragraph()

    notice = document.add_paragraph()
    notice.alignment = WD_ALIGN_PARAGRAPH.CENTER
    notice.paragraph_format.space_after = Pt(4)
    notice_run = notice.add_run("UNSIGNED PROPOSED DRAFT — REVIEW BEFORE SIGNING OR SHARING")
    notice_run.bold = True
    notice_run.font.size = Pt(9)
    disclosure_label = document.add_paragraph()
    disclosure_label_run = disclosure_label.add_run(PROPOSED_DISCLOSURE_LABEL)
    disclosure_label_run.bold = True
    disclosure_label_run.font.size = Pt(9)
    disclaimer = document.add_paragraph(PROPOSAL_BOUNDARY_DISCLOSURE)
    disclaimer.paragraph_format.space_after = Pt(8)
    intro = document.add_paragraph(
        "The following is a proposed settlement stipulation and agreement for the parties' "
        "review pursuant to CR 2A."
    )
    intro.paragraph_format.space_after = Pt(8)
    if terms.effective_date is not None:
        document.add_paragraph(f"Proposed effective date: {terms.effective_date.isoformat()}")
    if terms.response_by_date is not None:
        document.add_paragraph(f"Proposed response deadline: {terms.response_by_date.isoformat()}")

    def add_clause(number: str, text: str) -> None:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.25)
        paragraph.paragraph_format.first_line_indent = Inches(-0.25)
        label = paragraph.add_run(f"{number} ")
        label.bold = True
        paragraph.add_run(text)

    def add_section(title: str) -> None:
        heading = document.add_heading(title, level=2)
        heading.paragraph_format.keep_with_next = True
        heading.paragraph_format.space_before = Pt(8)
        heading.paragraph_format.space_after = Pt(3)

    add_section("I. PARENTING PLAN")
    add_clause("1.1", "Does not apply. This workflow is for a case without children.")
    add_section("II. CHILD SUPPORT")
    add_clause("2.1", "Does not apply. This workflow is for a case without children.")
    add_section("III. SPOUSAL MAINTENANCE")
    add_clause(
        "3.1",
        "Proposed maintenance terms: [Enter the parties' agreement or mark not applicable "
        "after review.]",
    )

    add_section("IV. PROPERTY ALLOCATION")
    add_clause(
        "4.1",
        f"Assets proposed to be awarded to {terms.offer_from}:",
    )
    for text in (
        "All personal property in that party's possession, except as otherwise stated herein.",
        "All bank accounts standing solely in that party's name, except as otherwise stated herein.",
        "Assets allocated to that party in the accompanying property-division schedule, "
        "to be reviewed and completed before signing.",
    ):
        document.add_paragraph(text, style="List Bullet")
    add_clause(
        "4.2",
        f"Assets proposed to be awarded to {terms.offer_to}:",
    )
    for text in (
        "All personal property in that party's possession, except as otherwise stated herein.",
        "All bank accounts standing solely in that party's name, except as otherwise stated herein.",
        "Assets allocated to that party in the accompanying property-division schedule, "
        "to be reviewed and completed before signing.",
    ):
        document.add_paragraph(text, style="List Bullet")
    add_clause(
        "4.3",
        "Each party shall promptly remove the other party from accounts and debts allocated "
        "to that party within [number] days after the agreement is signed, unless otherwise "
        "stated in the final agreement.",
    )
    add_clause(
        "4.4",
        "Property settlement payment, if any: [Identify the paying party, receiving party, "
        "amount, payment method, and due date(s).]",
    )
    add_clause("4.5", "Proposed terms and additional settlement provisions:")
    for term in terms.terms:
        document.add_paragraph(term, style="List Bullet")
    if terms.milestones:
        add_clause("4.6", "Attempt-specific milestones:")
        for milestone in terms.milestones:
            document.add_paragraph(
                f"{milestone.name}: {milestone.date.isoformat()}",
                style="List Bullet",
            )

    add_section("V. ALLOCATION OF DEBTS")
    add_clause(
        "5.1",
        "Each party shall pay debts incurred by that party after [separation date], except "
        "as otherwise stated in the final agreement.",
    )
    add_clause("5.2", f"Debts proposed to be allocated to {terms.offer_from}:")
    for text in (
        "Credit cards or loans in that party's name, unless otherwise stated herein.",
        "Liabilities associated with assets awarded to that party.",
        "Liabilities allocated to that party in the accompanying property-division schedule.",
    ):
        document.add_paragraph(text, style="List Bullet")
    add_clause("5.3", f"Debts proposed to be allocated to {terms.offer_to}:")
    for text in (
        "Credit cards or loans in that party's name, unless otherwise stated herein.",
        "Liabilities associated with assets awarded to that party.",
        "Liabilities allocated to that party in the accompanying property-division schedule.",
    ):
        document.add_paragraph(text, style="List Bullet")
    add_clause(
        "5.4",
        "Attorney fees and costs: [State the parties' proposed agreement regarding fees and costs.]",
    )

    add_section("VI. MISCELLANEOUS PROVISIONS")
    add_clause("6.1", "Marriage status or other requested finding: [Complete or remove after review.]")
    add_clause("6.2", "Pregnancy status, if relevant: [Complete or remove after review.]")
    add_clause(
        "6.3",
        "The parties acknowledge that the proposed agreement is fair and equitable "
        "[confirm or revise before signing].",
    )
    add_clause(
        "6.4",
        "Each party's representations concerning any property or interests not listed in "
        "this agreement: [Complete and review before signing.]",
    )
    add_clause(
        "6.5",
        "If a party does not pay a debt allocated to that party and a creditor seeks payment "
        "from the other party, the responsible party shall hold the other party harmless "
        "from that collection action, subject to the final agreement.",
    )
    add_clause(
        "6.6",
        "Preparation and review of final documents: [Identify the responsible counsel or "
        "party and the review process.]",
    )
    add_clause(
        "6.7",
        "Process for disputes about drafting or other unresolved issues: [Identify the "
        "process and decision-maker the parties choose; do not assume arbitration.]",
    )

    document.add_paragraph()
    witness = document.add_paragraph(
        "IN WITNESS WHEREOF, the parties and any counsel or mediator signing below intend "
        "to sign this proposed agreement on the date(s) entered below."
    )
    witness.paragraph_format.space_before = Pt(6)
    document.add_heading("SIGNATURES", level=2)
    signature_table = document.add_table(rows=6, cols=2)
    signature_table.style = "Table Grid"
    signature_table.autofit = False
    signature_column_widths = (Inches(3.25), Inches(3.25))
    for column, width in zip(signature_table.columns, signature_column_widths, strict=True):
        column.width = width
        for cell in column.cells:
            cell.width = width
    signature_rows = (
        (f"{terms.offer_from}\nProposing party", f"{terms.offer_to}\nOther party"),
        ("Signature: __________________________\nDate: __________________", "Signature: __________________________\nDate: __________________"),
        ("Counsel for proposing party (if applicable)\nSignature: __________________________", "Counsel for other party (if applicable)\nSignature: __________________________"),
        ("Date: __________________", "Date: __________________"),
        ("Mediator (if applicable)\nSignature: __________________________", "Additional signature, if applicable\nSignature: __________________________"),
        ("Date: __________________", "Date: __________________"),
    )
    for row, values in zip(signature_table.rows, signature_rows, strict=True):
        for cell, value in zip(row.cells, values, strict=True):
            cell.text = value
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(4)

    document.add_page_break()

    document.add_heading("Schedule A — Selected scenario property division", level=1)
    document.add_paragraph(
        "Amounts below are derived from the selected scenario's stated assumptions and "
        "ledger entries. They are proposals, not legal classifications or valuations."
    )
    document.add_paragraph(
        "Debt ledger balances are shown as positive liability amounts and are subtracted "
        "when calculating each party's illustrative net."
    )
    table = document.add_table(rows=1, cols=6)
    table.style = "Light Shading Accent 1"
    table.autofit = False
    schedule_widths = (
        Inches(1.65),
        Inches(0.7),
        Inches(1.05),
        Inches(1.05),
        Inches(0.95),
        Inches(0.9),
    )
    for column, width in zip(table.columns, schedule_widths, strict=True):
        column.width = width
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
    proposed_values = {
        str(value.asset_id): value.proposed_amount_cents
        for value in terms.proposed_values
    }
    if proposed_values:
        document.add_heading("Attempt-specific proposed values", level=2)
        ledger_names = {str(ledger.asset_id): ledger.name for ledger in result.ledgers}
        for asset_id, amount_cents in proposed_values.items():
            document.add_paragraph(
                f"{ledger_names.get(asset_id, asset_id)}: "
                f"{_currency(amount_cents)} proposed to {terms.offer_from}",
                style="List Bullet",
            )
    document.add_heading("Scenario assumptions", level=1)
    document.add_paragraph(
        f"{result.scenario.relationship_window.label}: "
        f"{result.scenario.relationship_window.start_date.isoformat()} through "
        f"{result.scenario.relationship_window.separation_date.isoformat()}."
    )
    document.add_paragraph(f"Tracing convention used: {result.scenario.tracing_method}.")
    document.add_paragraph(
        "Proposed community allocation: "
        f"{result.scenario.community_share_bps / 100:.2f}% to the offering party."
    )
    document.add_paragraph(
        "Review this schedule with the agreement. It is an illustrative export of the selected "
        "scenario, not a valuation, legal classification, signed exhibit, or court filing."
    )

    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _set_safe_text(cell, value: str) -> None:
    cell.value = value
    cell.data_type = "s"


OWNERSHIP_BAR_STEPS = 100
OWNERSHIP_USER_COLOR = "C0392B"
OWNERSHIP_OTHER_COLOR = "2F6DB5"
OWNERSHIP_NEUTRAL_COLOR = "D9D9D9"


def _add_ownership_bars(sheet, header_row: int, first_row: int, last_row: int) -> None:
    """Draw one red/blue split bar per row with conditional formatting so it follows edits."""
    pct_user_col, pct_other_col, bar_first_col = 10, 11, 12
    bar_last_col = bar_first_col + OWNERSHIP_BAR_STEPS - 1
    user_letter = get_column_letter(pct_user_col)
    other_letter = get_column_letter(pct_other_col)
    bar_first = get_column_letter(bar_first_col)
    bar_last = get_column_letter(bar_last_col)

    for column, label in ((pct_user_col, "User %"), (pct_other_col, "Other party %")):
        cell = sheet.cell(header_row, column)
        _set_safe_text(cell, label)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="527764")
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    sheet.merge_cells(
        start_row=header_row,
        start_column=bar_first_col,
        end_row=header_row,
        end_column=bar_last_col,
    )
    bar_header = sheet.cell(header_row, bar_first_col)
    _set_safe_text(bar_header, "Ownership split (red = user, blue = other party)")
    bar_header.font = Font(bold=True, color="FFFFFF")
    bar_header.fill = PatternFill("solid", fgColor="527764")
    bar_header.alignment = Alignment(vertical="center")

    legend_row = header_row - 1
    sheet.merge_cells(start_row=legend_row, start_column=1, end_row=legend_row, end_column=9)
    _set_safe_text(
        sheet.cell(legend_row, 1),
        "Ownership bars show each row's proposed amount to the user versus the other party "
        "(Proposed ÷ Total). Grey means no split can be shown. They update when proposed amounts change.",
    )
    sheet.row_dimensions[legend_row].height = 32
    for column, label, color in (
        (pct_user_col, "User", OWNERSHIP_USER_COLOR),
        (pct_other_col, "Other party", OWNERSHIP_OTHER_COLOR),
    ):
        swatch = sheet.cell(legend_row, column)
        _set_safe_text(swatch, label)
        swatch.font = Font(bold=True, color="FFFFFF")
        swatch.fill = PatternFill("solid", fgColor=color)

    for row_number in range(first_row, last_row + 1):
        sheet.cell(
            row_number,
            pct_user_col,
            f'=IF(G{row_number}>0,MAX(0,MIN(1,H{row_number}/G{row_number})),"")',
        )
        sheet.cell(
            row_number,
            pct_other_col,
            f'=IF(ISNUMBER({user_letter}{row_number}),1-{user_letter}{row_number},"")',
        )
        sheet.cell(row_number, pct_user_col).number_format = "0%"
        sheet.cell(row_number, pct_other_col).number_format = "0%"

    bar_range = f"{bar_first}{first_row}:{bar_last}{last_row}"
    position = f"(COLUMN()-COLUMN(${bar_first}${first_row})+1)"
    share = f"ROUND(${user_letter}{first_row}*{OWNERSHIP_BAR_STEPS},0)"
    rules = (
        (f"AND(ISNUMBER(${user_letter}{first_row}),{position}<={share})", OWNERSHIP_USER_COLOR),
        (f"AND(ISNUMBER(${user_letter}{first_row}),{position}>{share})", OWNERSHIP_OTHER_COLOR),
        (f"NOT(ISNUMBER(${user_letter}{first_row}))", OWNERSHIP_NEUTRAL_COLOR),
    )
    for formula, color in rules:
        sheet.conditional_formatting.add(
            bar_range,
            FormulaRule(
                formula=[formula],
                fill=PatternFill(start_color=color, end_color=color, fill_type="solid"),
                stopIfTrue=True,
            ),
        )
    for column in range(bar_first_col, bar_last_col + 1):
        sheet.column_dimensions[get_column_letter(column)].width = 0.4
    for column, width in ((pct_user_col, 10), (pct_other_col, 14)):
        sheet.column_dimensions[get_column_letter(column)].width = width


def render_property_schedule_xlsx(
    terms: MediationOfferTerms,
    result: SettlementScenarioResult,
) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Property Division"
    assumptions = workbook.create_sheet("Scenario Assumptions")
    review = workbook.create_sheet("Important review", 0)
    workbook.active = 0
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True

    review.merge_cells("A1:F1")
    _set_safe_text(review["A1"], PROPOSED_DISCLOSURE_LABEL)
    review["A1"].font = Font(bold=True, color="FFFFFF")
    review["A1"].fill = PatternFill("solid", fgColor="8A4B23")
    review["A1"].alignment = Alignment(wrap_text=True, vertical="top")
    review.row_dimensions[1].height = 30
    review.merge_cells("A2:F2")
    _set_safe_text(review["A2"], PROPOSAL_BOUNDARY_DISCLOSURE)
    review["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    review.row_dimensions[2].height = 100
    review.merge_cells("A3:F3")
    _set_safe_text(
        review["A3"],
        "This workbook is an unsigned proposed schedule. Amounts and allocations are "
        "arithmetic outputs based on the selected scenario and entered assumptions, not "
        "legal classifications, valuations, findings, or a prediction.",
    )
    review["A3"].alignment = Alignment(wrap_text=True, vertical="top")
    review.row_dimensions[3].height = 54
    for column in range(1, 7):
        review.column_dimensions[get_column_letter(column)].width = 18

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
    proposed_values = {
        str(value.asset_id): value.proposed_amount_cents
        for value in terms.proposed_values
    }
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
        proposed_amount = proposed_values.get(str(ledger.asset_id))
        if proposed_amount is None:
            sheet.cell(row_number, 8, f"=C{row_number}+E{row_number}*'Scenario Assumptions'!$B$6")
        else:
            sheet.cell(row_number, 8, proposed_amount / 100)
        sheet.cell(row_number, 9, f"=G{row_number}-H{row_number}")

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
    _add_ownership_bars(sheet, header_row, first_data_row, last_data_row)
    sheet.freeze_panes = f"A{first_data_row}"
    sheet.auto_filter.ref = f"A{header_row}:I{last_data_row}"
    sheet.row_dimensions[header_row].height = 34
    for column, width in enumerate((34, 14, 17, 20, 17, 17, 17, 19, 22), 1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    for row in sheet.iter_rows(min_row=1, max_row=total_row + 3, max_col=9):
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

    if terms.milestones:
        milestones = workbook.create_sheet("Attempt Milestones")
        for column, label in enumerate(("Milestone", "Date"), 1):
            cell = milestones.cell(1, column)
            _set_safe_text(cell, label)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="527764")
        for row_number, milestone in enumerate(terms.milestones, 2):
            _set_safe_text(milestones.cell(row_number, 1), milestone.name)
            milestones.cell(row_number, 2, milestone.date)
            milestones.cell(row_number, 2).number_format = "yyyy-mm-dd"
        milestones.column_dimensions["A"].width = 38
        milestones.column_dimensions["B"].width = 18
        milestones.freeze_panes = "A2"

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
