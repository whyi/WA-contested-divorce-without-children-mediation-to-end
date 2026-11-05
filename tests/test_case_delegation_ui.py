import re
import unittest
from pathlib import Path

PAGE = (Path(__file__).parents[1] / "src" / "app" / "static" / "index.html").read_text()


class CaseDelegationUiTests(unittest.TestCase):
    def test_signup_offers_unverified_account_type_choice(self) -> None:
        self.assertRegex(PAGE, r'<select id="signup-account-type" name="account_type">')
        self.assertIn('<option value="party" selected>', PAGE)
        self.assertIn('<option value="professional">', PAGE)
        self.assertIn("self-declared and are not verified", PAGE)

    def test_delegation_panel_is_labelled_with_live_status(self) -> None:
        self.assertRegex(PAGE, r'<section[^>]*id="case-delegation"[^>]*aria-labelledby="case-delegation-title"')
        self.assertRegex(PAGE, r'id="case-delegation-current"[^>]*role="status"[^>]*aria-live="polite"')
        self.assertRegex(PAGE, r'id="delegation-accept-status"[^>]*role="status"[^>]*aria-live="polite"')
        self.assertIn('for="case-delegation-email"', PAGE)

    def test_copy_keeps_one_side_boundary_and_makes_no_legal_claim(self) -> None:
        panel = PAGE[PAGE.index('id="case-delegation"') :][:1800]
        self.assertIn("The other party is never invited", panel)
        self.assertIn("does not verify anyone's identity or legal authority", panel)
        self.assertIn("Only one account can use the case at a time", panel)
        self.assertNotRegex(panel, r"(?i)collaborat|share with the other")

    def test_ui_uses_delegation_api_with_csrf_through_settlement_api(self) -> None:
        self.assertIn("/delegation`", PAGE)
        self.assertIn('method: "DELETE"', PAGE[PAGE.index("async function revokeCaseDelegate") :][:600])
        self.assertIn("/api/v1/delegations/accept", PAGE)
        self.assertIn("...(options.method && options.method !== \"GET\" ? csrfHeaders() : {})", PAGE)

    def test_workspace_loads_delegation_and_hides_panel_for_delegates(self) -> None:
        opener = PAGE[PAGE.index("async function openSettlementPlanner") :][:200]
        self.assertIn("loadCaseDelegation(caseId)", opener)
        loader = PAGE[PAGE.index("async function loadCaseDelegation") :][:600]
        self.assertRegex(loader, r"catch \(error\) \{\s*caseDelegation\.hidden = true;")


if __name__ == "__main__":
    unittest.main()
