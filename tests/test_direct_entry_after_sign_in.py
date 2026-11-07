import re
import unittest
from pathlib import Path

PAGE = (Path(__file__).parents[1] / "src" / "app" / "static" / "index.html").read_text(
    encoding="utf-8"
)


def _function_body(name: str) -> str:
    match = re.search(rf"(?:async )?function {name}\(", PAGE)
    assert match is not None, name
    start = PAGE.index(") {", match.end()) + 2
    depth = 0
    for index in range(start, len(PAGE)):
        if PAGE[index] == "{":
            depth += 1
        elif PAGE[index] == "}":
            depth -= 1
            if depth == 0:
                return PAGE[start : index + 1]
    raise AssertionError(f"{name} is not closed")


class DirectEntryAfterSignInTests(unittest.TestCase):
    def test_case_list_page_is_removed(self) -> None:
        for removed in (
            "Active cases",
            "Your workspace",
            "existing-cases-title",
            'id="case-list"',
            "existing-case-count",
            "function renderCases",
            "case-tile-new",
        ):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, PAGE.replace(".case-tile-new {", "", 1) if removed == "case-tile-new" else PAGE)

    def test_signed_in_entry_chooses_between_account_tools_case_and_new_case(self) -> None:
        body = _function_body("enterSignedInAccount")

        order = [
            body.index("accountToolsMode"),
            body.index("openActiveCase(account.cases[0])"),
            body.index("await loadClosedCases() > 0"),
            body.index("showNewCaseStart()"),
        ]
        self.assertEqual(order, sorted(order))
        self.assertIn("account.active_case_count > 0", body)

    def test_active_case_opens_with_replace_navigation_and_keeps_loading_state(self) -> None:
        body = _function_body("openActiveCase")

        self.assertIn("window.location.replace(", body)
        self.assertNotIn("location.assign", body)
        self.assertIn("/onboarding/${item.workflow_mode}?case_id=", body)
        redirect = body.index("window.location.replace(")
        self.assertLess(redirect, body.index("dashboardLoading.hidden = true"))
        self.assertIn("openSettlementPlanner(item.id)", body)

    def test_new_case_choice_opens_immediately_and_leaves_a_start_action(self) -> None:
        body = _function_body("showNewCaseStart")

        self.assertIn("newCaseEntry.hidden = false", body)
        self.assertIn("openCaseCreationDialog()", body)
        self.assertRegex(
            PAGE,
            re.compile(
                r'<section class="new-case-entry" id="new-case-entry"[^>]*hidden>.*?'
                r'id="new-case-start"[^>]*>Start a new case</button>',
                re.S,
            ),
        )
        self.assertIn('newCaseStart.addEventListener("click", openCaseCreationDialog)', PAGE)

    def test_dashboard_status_routes_through_direct_entry_without_the_header(self) -> None:
        body = _function_body("loadDashboardStatus")

        self.assertLess(
            body.index('document.getElementById("dashboard-header").hidden = true'),
            body.index('fetch("/api/v1/dashboard/status"'),
        )
        self.assertIn("await enterSignedInAccount(account)", body)
        self.assertEqual(body.count("void loadAttemptCreditPackages();"), 1)

    def test_account_tools_are_reachable_without_redirecting(self) -> None:
        self.assertRegex(
            PAGE,
            r'<a class="nav-cta account-tools-link" id="account-tools-link" href="/\?view=account" hidden>Account</a>',
        )
        self.assertIn('new URLSearchParams(window.location.search).get("view") === "account"', PAGE)
        section = re.search(
            r'<section class="account-tools" id="account-tools"[^>]*hidden>(.*?)\n            </section>\n            <section class="new-case-entry"',
            PAGE,
            re.S,
        )
        self.assertIsNotNone(section)
        self.assertIn('id="closed-cases"', section.group(1))
        self.assertIn('id="account-permanent-deletion"', section.group(1))
        existing = PAGE[PAGE.index('id="existing-cases"') :]
        self.assertLess(existing.index('id="case-create-dialog"'), existing.index('id="settlement-planner"'))
        self.assertNotIn('id="closed-cases"', existing)

    def test_return_wording_no_longer_refers_to_a_case_list(self) -> None:
        self.assertIn('wizardFinish.textContent = "Save draft";', PAGE)
        self.assertNotIn("return to cases", PAGE)
        self.assertNotIn("Return to your cases", PAGE)


if __name__ == "__main__":
    unittest.main()
