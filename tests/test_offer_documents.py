import unittest
from io import BytesIO
from uuid import uuid4

from docx import Document
from openpyxl import load_workbook
from pydantic import ValidationError

from app.offer_documents import (
    MediationOfferTerms,
    PROPOSED_DISCLOSURE_LABEL,
    PROPOSAL_BOUNDARY_DISCLOSURE,
    render_mediation_offer_docx,
    render_property_schedule_xlsx,
)
from app.settlement_planning import (
    AssetLedger,
    LedgerEvent,
    RelationshipWindow,
    ScenarioAxes,
    calculate_scenario,
    generate_scenarios,
)


class MediationOfferDocumentTests(unittest.TestCase):
    def setUp(self) -> None:
        window = RelationshipWindow(
            id="marriage",
            label="Marriage-only dates",
            relationship_type="marriage_only",
            start_date="2020-01-01",
            separation_date="2024-01-01",
        )
        scenario = generate_scenarios(
            ScenarioAxes(
                relationship_windows=[window],
                tracing_methods=["explicit"],
                community_share_bps=[6_000],
            )
        )[0]
        self.result = calculate_scenario(
            scenario,
            [
                AssetLedger(
                    asset_id=uuid4(),
                    name="Savings",
                    kind="asset",
                    events=[
                        LedgerEvent(
                            effective_date="2022-01-01",
                            event_type="contribution",
                            amount_cents=10_000,
                            source_allocations={"community": 10_000},
                            provenance="user_reported",
                        )
                    ],
                )
            ],
        )

    def test_creates_editable_unsigned_docx_without_private_source_notes(self) -> None:
        terms = MediationOfferTerms(
            offer_from="You",
            offer_to="Other party",
            effective_date="2026-01-01",
            response_by_date="2026-02-01",
            terms=["Each party keeps their own retirement account."],
        )

        payload = render_mediation_offer_docx(terms, self.result)
        document = Document(BytesIO(payload))
        paragraphs = "\n".join(paragraph.text for paragraph in document.paragraphs)
        table_text = "\n".join(
            cell.text
            for table in document.tables
            for row in table.rows
            for cell in row.cells
        )
        all_text = f"{paragraphs}\n{table_text}"

        self.assertIn("UNSIGNED PROPOSED DRAFT", paragraphs)
        self.assertIn(PROPOSED_DISCLOSURE_LABEL, paragraphs)
        self.assertIn(PROPOSAL_BOUNDARY_DISCLOSURE, paragraphs)
        self.assertIn("not legal advice or representation", paragraphs)
        self.assertIn("not filed", paragraphs)
        self.assertIn("any particular outcome", paragraphs)
        self.assertIn("provide it to your mediator", paragraphs)
        self.assertIn("does not automatically deliver proposals", paragraphs)
        self.assertIn("CR 2A AGREEMENT", all_text)
        self.assertIn("IN THE SUPERIOR COURT OF THE STATE OF WASHINGTON", paragraphs)
        self.assertIn("FOR [COUNTY] COUNTY", paragraphs)
        self.assertIn("proposed settlement stipulation and agreement", paragraphs)
        self.assertIn("Proposed effective date: 2026-01-01", paragraphs)
        self.assertIn("Proposed response deadline: 2026-02-01", paragraphs)
        self.assertIn("I. PARENTING PLAN", paragraphs)
        self.assertIn("II. CHILD SUPPORT", paragraphs)
        self.assertIn("III. SPOUSAL MAINTENANCE", paragraphs)
        self.assertIn("IV. PROPERTY ALLOCATION", paragraphs)
        self.assertIn("V. ALLOCATION OF DEBTS", paragraphs)
        self.assertIn("VI. MISCELLANEOUS PROVISIONS", paragraphs)
        self.assertIn("4.5 Proposed terms and additional settlement provisions:", paragraphs)
        self.assertIn("Each party keeps their own retirement account.", paragraphs)
        self.assertIn("SIGNATURES", paragraphs)
        self.assertIn("Schedule A — Selected scenario property division", paragraphs)
        self.assertIn("Scenario assumptions", paragraphs)
        self.assertIn("User separate", table_text)
        self.assertIn("Savings", table_text)
        self.assertIn("60.00% to the offering party", paragraphs)
        self.assertIn("You", document.tables[0].cell(0, 0).text)
        self.assertIn("Other party", document.tables[0].cell(0, 0).text)
        self.assertIn("You", document.tables[1].cell(0, 0).text)
        self.assertIn("Other party", document.tables[1].cell(0, 1).text)
        page_breaks = [
            index
            for index, paragraph in enumerate(document.paragraphs)
            if paragraph._p.xpath('.//w:br[@w:type="page"]')
        ]
        schedule_index = next(
            index
            for index, paragraph in enumerate(document.paragraphs)
            if paragraph.text == "Schedule A — Selected scenario property division"
        )
        self.assertTrue(page_breaks)
        self.assertLess(page_breaks[0], schedule_index)
        self.assertNotIn("Internal review notes", paragraphs)
        self.assertNotIn("source quote", paragraphs.lower())

    def test_creates_editable_property_schedule_with_formula_totals_and_assumptions(self) -> None:
        terms = MediationOfferTerms(
            offer_from="You",
            offer_to="Other party",
            terms=["Each party keeps their own retirement account."],
        )

        payload = render_property_schedule_xlsx(terms, self.result)
        workbook = load_workbook(BytesIO(payload), data_only=False)
        sheet = workbook["Property Division"]
        assumptions = workbook["Scenario Assumptions"]
        review = workbook["Important review"]

        self.assertEqual(sheet["A5"].value, "Property or debt")
        self.assertEqual(sheet["B5"].value, "Type")
        self.assertEqual(sheet["A6"].value, "Savings")
        self.assertEqual(sheet["G6"].value, "=SUM(C6:F6)")
        self.assertEqual(
            sheet["H6"].value,
            "=C6+E6*'Scenario Assumptions'!$B$6",
        )
        self.assertTrue(sheet["H7"].value.startswith("=SUM(H6:H6)"))
        self.assertEqual(assumptions["A1"].value, "Scenario assumption")
        self.assertEqual(assumptions["A2"].value, "Scenario")
        self.assertEqual(assumptions["B6"].value, 0.6)
        self.assertEqual(sheet["A10"].value, "Net unresolved (assets less debts)")
        self.assertIn("SUMIF", sheet["F10"].value)
        self.assertEqual(sheet.freeze_panes, "A6")
        self.assertEqual(workbook.active.title, "Important review")
        self.assertEqual(review["A1"].value, PROPOSED_DISCLOSURE_LABEL)
        self.assertEqual(review["A2"].value, PROPOSAL_BOUNDARY_DISCLOSURE)
        self.assertIn("not legal classifications", review["A3"].value)

    def test_workbook_treats_user_supplied_asset_names_as_text(self) -> None:
        from app.settlement_planning import AssetLedger, LedgerEvent, calculate_scenario

        malicious_name = "=HYPERLINK(\"https://example.invalid\",\"click\")"
        result = calculate_scenario(
            self.result.scenario,
            [
                AssetLedger(
                    asset_id=uuid4(),
                    name=malicious_name,
                    kind="asset",
                    events=[
                        LedgerEvent(
                            effective_date="2022-01-01",
                            event_type="contribution",
                            amount_cents=10_000,
                            source_allocations={"community": 10_000},
                            provenance="user_reported",
                        )
                    ],
                )
            ],
        )
        terms = MediationOfferTerms(
            offer_from="You",
            offer_to="Other party",
            terms=["Review."],
        )

        workbook = load_workbook(
            BytesIO(render_property_schedule_xlsx(terms, result)),
            data_only=False,
        )
        name_cell = workbook["Property Division"]["A6"]
        self.assertEqual(name_cell.value, malicious_name)
        self.assertEqual(name_cell.data_type, "s")

    def test_rejects_blank_offer_terms_and_invalid_dates(self) -> None:
        with self.assertRaises(ValidationError):
            MediationOfferTerms(
                offer_from=" ",
                offer_to="Other party",
                terms=["Offer"],
            )
        with self.assertRaises(ValidationError):
            MediationOfferTerms(
                offer_from="You",
                offer_to="Other party",
                effective_date="2024-02-30",
                terms=["Offer"],
            )
        with self.assertRaises(ValidationError):
            MediationOfferTerms(
                offer_from="You",
                offer_to="Other party",
                effective_date="2026-02-02",
                response_by_date="2026-02-01",
                terms=["Offer"],
            )
        with self.assertRaises(ValidationError):
            MediationOfferTerms(
                offer_from="You",
                offer_to="Other party",
                terms=["x" * 2_001],
            )
        with self.assertRaises(ValidationError):
            MediationOfferTerms(
                offer_from="You\x00",
                offer_to="Other party",
                terms=["Offer"],
            )


if __name__ == "__main__":
    unittest.main()
