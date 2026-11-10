import unittest
from html.parser import HTMLParser
from pathlib import Path


PAGE = (Path(__file__).parents[1] / "src/app/static/index.html").read_text(
    encoding="utf-8"
)


class CaseMarkup(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element_id = dict(attrs).get("id")
        if element_id is not None:
            self.ids.append(element_id)


class RemovedNegotiationPlannerTests(unittest.TestCase):
    def test_real_account_proposal_workspace_and_editable_controls_are_present(self) -> None:
        for required in (
            "Negotiation attempts",
            'id="settlement-planner"',
            'id="settlement-offer-values"',
            'id="settlement-axes-json"',
            'id="settlement-generate"',
            'id="settlement-offer-download"',
            'id="settlement-finalize-download"',
            "openSettlementPlanner",
            "finalizeSettlementAttempt",
            "renderSettlementOfferComparison",
        ):
            with self.subTest(required=required):
                self.assertTrue(required in PAGE, f"Missing required workspace element: {required}")

    def test_authenticated_case_entry_preserves_preparation_and_offers_explicit_workspace_entry(self) -> None:
        entry = PAGE.split("async function openActiveCase(item)", 1)[1].split(
            "\n        function showAccountTools()", 1
        )[0]
        self.assertIn("/onboarding/${item.workflow_mode}", entry)
        self.assertNotIn("openSettlementPlanner(item.id)", entry)
        self.assertIn('id="open-proposal-workspace"', PAGE)
        self.assertIn("openSettlementPlanner(preparationCaseId || settlementCaseId)", PAGE)
        self.assertIn("/settlement-planning", PAGE)
        self.assertIn("credentials: \"same-origin\"", PAGE)
        self.assertIn("The product does not automatically deliver proposals", PAGE)
        self.assertNotIn("optional external transfer", PAGE)

    def test_case_actions_exist_once_inside_account_not_the_deleted_page(self) -> None:
        markup = CaseMarkup()
        markup.feed(PAGE)
        account = PAGE.split('id="account-tools"', 1)[1].split(
            'id="new-case-entry"', 1
        )[0]
        for element_id in (
            "account-active-case-list",
            "settlement-case-close",
            "settlement-case-delete",
            "settlement-case-action-status",
        ):
            self.assertEqual(markup.ids.count(element_id), 1)
            self.assertIn(f'id="{element_id}"', account)

    def test_saved_case_information_and_real_document_controls_remain(self) -> None:
        for element_id in (
            "documents-demo",
            "demo-file-input",
            "wizard-demo",
            "wizard-finish",
            "existing-offer-panel",
        ):
            self.assertIn(f'id="{element_id}"', PAGE)
        self.assertIn('id="wizard-finish" type="button" disabled>Next</button>', PAGE)
        self.assertIn("/workspace-entry", PAGE)
        self.assertIn("await uploadCaseFiles(caseSelectedDocuments)", PAGE)
        self.assertIn("startPathPage.hidden = false", PAGE)

    def test_demo_and_existing_completion_features_remain_independent(self) -> None:
        for element_id in (
            "asset-analysis-view",
            "settlement-scenario-results",
            "settlement-demo-docx-download",
            "settlement-demo-response-preview",
            "settlement-completion-page",
        ):
            self.assertIn(f'id="{element_id}"', PAGE)
        self.assertNotIn("/offer-response/attachments/accepted_offer", PAGE)
        self.assertIn('response.outcome !== "accepted" || !response.sent_confirmed', PAGE)
        self.assertIn('id="settlement-completion-close-case"', PAGE)
        self.assertIn("/offer-response/complete", PAGE)


if __name__ == "__main__":
    unittest.main()
