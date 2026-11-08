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
    def test_workspace_remnants_are_deleted_not_hidden(self) -> None:
        for forbidden in ("Your case workspace", "dashboard-header", "dashboard-title", "dashboard-intro"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, PAGE)
        self.assertIn('id="demo-workspace-header" hidden', PAGE)
        self.assertIn('id="demo-workspace-title">Demo case</h1>', PAGE)
        self.assertIn('document.getElementById("demo-workspace-title").textContent = demoCaseData?.title', PAGE)
        self.assertIn('"/onboarding/upload": "upload"', PAGE)
        self.assertIn('id="materials-workflow"', PAGE)

    def test_ci_requires_executable_chromium_entry_regressions(self) -> None:
        root = Path(__file__).parents[1]
        workflow = (root / ".github/workflows/test.yml").read_text(encoding="utf-8")
        browser_job = workflow.split("  entry-regressions:", 1)[1].split("  test:", 1)[0]
        self.assertIn("runs-on: ubuntu-24.04", browser_job)
        self.assertIn("run: npm ci", browser_job)
        self.assertIn("run: npx playwright install --with-deps chromium", browser_job)
        self.assertIn("run: npm run entry", browser_job)
        self.assertNotIn("continue-on-error", browser_job)
        self.assertNotIn("if:", browser_job)
        self.assertTrue((root / "uat/entry.spec.js").is_file())
        self.assertIn('testMatch: "entry.spec.js"', (root / "uat/entry.config.js").read_text(encoding="utf-8"))

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

    def test_active_case_opens_attempts_without_preparation_redirect(self) -> None:
        body = _function_body("openActiveCase")

        self.assertNotIn("window.location", body)
        self.assertNotIn("wizardIntakeComplete", body)
        self.assertNotIn("wizard-intake", body)
        self.assertIn("/onboarding/${item.workflow_mode}?case_id=", body)
        self.assertLess(body.index("dashboardLoading.hidden = true"), body.index("await openSettlementPlanner(item.id)"))
        self.assertIn("settlementEditIntake.hidden = !startUrl", body)

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

    def test_dashboard_status_routes_through_direct_entry_without_workspace_markup(self) -> None:
        body = _function_body("loadDashboardStatus")

        self.assertNotIn("dashboard-header", body)
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
        self.assertIn('wizardFinish.textContent = "Save and continue";', PAGE)
        self.assertNotIn("return to cases", PAGE)
        self.assertNotIn("Return to your cases", PAGE)


if __name__ == "__main__":
    unittest.main()
