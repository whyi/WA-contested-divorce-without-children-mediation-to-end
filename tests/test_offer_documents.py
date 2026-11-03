import unittest
from io import BytesIO
from uuid import uuid4

from docx import Document
from pydantic import ValidationError

from app.offer_documents import MediationOfferTerms, render_mediation_offer_docx
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

    def test_creates_editable_nonbinding_docx_without_private_source_notes(self) -> None:
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

        self.assertIn("NONBINDING DRAFT", paragraphs)
        self.assertIn("not a court filing", paragraphs)
        self.assertIn("User separate", table_text)
        self.assertIn("Savings", table_text)
        self.assertIn("60.00% to the offering party", paragraphs)
        self.assertNotIn("Internal review notes", paragraphs)
        self.assertNotIn("source quote", paragraphs.lower())

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


if __name__ == "__main__":
    unittest.main()
