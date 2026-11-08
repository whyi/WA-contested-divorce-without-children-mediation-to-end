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
    def test_deleted_page_and_technical_controls_are_absent_even_when_hidden(self) -> None:
        for removed in (
            "Negotiation attempts",
            "Attempt workspace ready.",
            "Advanced evidence and ledger tools",
            "Separate consent for settlement planning",
            "Append ledger events",
            "Scenario assumptions JSON",
            "Calculate and rank scenarios",
            "settlement-planner",
            "settlement-ledger-json",
            "settlement-axes-json",
            "settlement-generate",
            "openSettlementPlanner",
            "createWizardAttemptOne",
            "settlement-edit-intake",
        ):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, PAGE)

    def test_case_actions_exist_once_inside_account_not_the_deleted_page(self) -> None:
        markup = CaseMarkup()
        markup.feed(PAGE)
        account = PAGE.split('id="account-tools"', 1)[1].split(
            'id="new-case-entry"', 1
        )[0]
        for element_id in (
            "settlement-case-export",
            "settlement-case-close",
            "settlement-case-delete",
            "settlement-case-action-status",
        ):
            self.assertEqual(markup.ids.count(element_id), 1)
            self.assertIn(f'id="{element_id}"', account)

    def test_saved_case_information_and_real_document_controls_remain(self) -> None:
        for element_id in (
            "materials-workflow",
            "materials-file-input",
            "wizard-demo",
            "wizard-finish",
            "existing-offer-panel",
            "existing-offer-toggle",
        ):
            self.assertIn(f'id="{element_id}"', PAGE)
        self.assertIn('wizardFinish.textContent = "Save case information"', PAGE)
        self.assertIn("Your case information is saved.", PAGE)
        self.assertIn("Your offer choice is saved.", PAGE)
        self.assertIn("startPathDialog.showModal()", PAGE)

    def test_demo_and_existing_completion_features_remain_independent(self) -> None:
        for element_id in (
            "asset-analysis-view",
            "settlement-scenario-results",
            "settlement-demo-docx-download",
            "settlement-demo-response-preview",
            "settlement-completion-page",
            "settlement-response-accepted-file",
        ):
            self.assertIn(f'id="{element_id}"', PAGE)
        self.assertIn("/offer-response/attachments/accepted_offer", PAGE)
        self.assertIn('response.outcome !== "accepted" || !response.sent_confirmed', PAGE)
        self.assertIn("/offer-response/complete", PAGE)


if __name__ == "__main__":
    unittest.main()
