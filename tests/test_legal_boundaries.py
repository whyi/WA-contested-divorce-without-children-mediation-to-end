import re
import unittest
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from docx import Document
from openpyxl import load_workbook

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

ROOT = Path(__file__).parents[1]
PAGE = (ROOT / "src" / "app" / "static" / "index.html").read_text()


def _sample_result():
    scenario = generate_scenarios(
        ScenarioAxes(
            relationship_windows=[
                RelationshipWindow(
                    id="window",
                    label="User-entered date range",
                    relationship_type="marriage_only",
                    start_date="2020-01-01",
                    separation_date="2024-01-01",
                )
            ],
            tracing_methods=["explicit"],
            community_share_bps=[5_000],
        )
    )[0]
    return calculate_scenario(
        scenario,
        [
            AssetLedger(
                asset_id=uuid4(),
                name="Example account",
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


class LegalBoundaryDisclosureTests(unittest.TestCase):
    def test_marketing_and_onboarding_disclosures_are_explicitly_proposed(self) -> None:
        marketing_start = PAGE.index('class="homepage-expectations"')
        onboarding_start = PAGE.index('id="case-create-dialog"')
        marketing = PAGE[marketing_start:onboarding_start]
        onboarding_end = PAGE.index("</dialog>", onboarding_start)
        onboarding = PAGE[onboarding_start:onboarding_end]

        for surface in (marketing, onboarding):
            self.assertIn("pending qualified counsel review", surface.lower())
            self.assertIn("not legal advice or representation", surface.lower())
            self.assertIn("cannot guarantee correctness, fairness, acceptance", surface.lower())
            self.assertIn("provide it to your mediator", surface.lower())
            self.assertIn("downloading is not delivery", surface.lower())
            self.assertIn("does not automatically deliver", surface.lower())

    def test_ai_calculations_comparison_and_finalization_are_bounded(self) -> None:
        analysis_start = PAGE.index('id="analysis-controls"')
        analysis_end = PAGE.index('id="proposal-review"', analysis_start)
        analysis = PAGE[analysis_start:analysis_end]
        self.assertIn("may be incomplete or incorrect", analysis)
        self.assertIn("not verified facts or legal advice", analysis)

        comparison_start = PAGE.index('id="settlement-offer-comparison"')
        comparison_end = PAGE.index("</section>", comparison_start)
        comparison = PAGE[comparison_start:comparison_end]
        self.assertIn("compare saved values arithmetically", comparison)
        self.assertIn("do not classify property", comparison)
        self.assertIn("not legal classifications", PAGE[PAGE.index('id="settlement-planner"'):comparison_start])

        finalization_start = PAGE.index('id="settlement-finalize-note"')
        finalization_end = PAGE.index("</p>", finalization_start)
        finalization = PAGE[finalization_start:finalization_end]
        self.assertIn("not legal review, delivery, filing, or proof of receipt", finalization)
        self.assertIn("provide them to your mediator", finalization)
        self.assertIn("does not automatically deliver them", finalization)

    def test_completion_guidance_does_not_imply_legal_resolution_or_delivery(self) -> None:
        accepted_start = PAGE.index('id="settlement-completion-page"')
        rejected_start = PAGE.index('id="rejection-completion-page"')
        accepted = PAGE[accepted_start:rejected_start]
        rejected_end = PAGE.index("</section>", rejected_start)
        rejected = PAGE[rejected_start:rejected_end]

        for surface in (accepted, rejected):
            self.assertIn("pending qualified counsel review", surface.lower())
            self.assertIn("does not provide legal advice", surface.lower())
            self.assertIn("does not guarantee any outcome", surface.lower())
            self.assertIn("downloading", surface.lower())
            self.assertIn("does not automatically deliver proposals", surface.lower())
        self.assertIn("does not itself establish legal resolution", accepted)
        self.assertIn("does not resolve or end your divorce case", rejected)

    def test_generated_docx_and_workbook_carry_the_same_pending_disclosure(self) -> None:
        terms = MediationOfferTerms(
            offer_from="User party",
            offer_to="Other party",
            terms=["Proposed division for review."],
        )
        result = _sample_result()
        docx = Document(BytesIO(render_mediation_offer_docx(terms, result)))
        docx_text = "\n".join(paragraph.text for paragraph in docx.paragraphs)
        self.assertIn(PROPOSED_DISCLOSURE_LABEL, docx_text)
        self.assertIn(PROPOSAL_BOUNDARY_DISCLOSURE, docx_text)

        workbook = load_workbook(
            BytesIO(render_property_schedule_xlsx(terms, result)),
            data_only=False,
        )
        self.assertEqual(workbook.active.title, "Important review")
        self.assertEqual(workbook["Important review"]["A1"].value, PROPOSED_DISCLOSURE_LABEL)
        self.assertEqual(
            workbook["Important review"]["A2"].value,
            PROPOSAL_BOUNDARY_DISCLOSURE,
        )
        for text in (docx_text, workbook["Important review"]["A2"].value):
            self.assertIn("not legal advice or representation", text)
            self.assertIn("cannot guarantee correctness, fairness, acceptance", text)
            self.assertIn("provide it to your mediator", text)
            self.assertIn("does not automatically deliver proposals", text)

    def test_product_copy_makes_no_unsubstantiated_approval_or_auto_delivery_claim(self) -> None:
        product_copy = PAGE.lower()
        self.assertIsNone(
            re.search(r"\b(?:attorney|counsel)[ -](?:approved|reviewed)\b", product_copy)
        )
        self.assertNotIn("the app never sends anything to the other party", product_copy)
        self.assertIn("optional file-transfer controls", product_copy)
        self.assertIn("do not verify mediator receipt", product_copy)
        self.assertIn("downloading is not delivery", product_copy)
        self.assertNotIn("a download means the proposal was delivered", product_copy)


if __name__ == "__main__":
    unittest.main()
