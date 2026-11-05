import re
import unittest
from pathlib import Path

PAGE = (Path(__file__).parents[1] / "src" / "app" / "static" / "index.html").read_text()


class ClosedCaseDashboardTests(unittest.TestCase):
    def test_dashboard_lists_closed_cases_with_accessible_reopen_and_export(self) -> None:
        section = re.search(r'<section[^>]*id="closed-cases"[^>]*>', PAGE)
        self.assertIsNotNone(section)
        self.assertIn("aria-labelledby=\"closed-cases-title\"", section.group(0))
        self.assertIn('id="closed-cases-status"', PAGE)
        self.assertRegex(PAGE, r'id="closed-cases-status"[^>]*role="status"[^>]*aria-live="polite"')
        self.assertIn("/api/v1/closed-cases", PAGE)
        self.assertIn("/reopen", PAGE)
        self.assertIn("Reopen ${", PAGE)
        self.assertIn("Export all data for ${", PAGE)

    def test_closed_case_copy_says_nothing_is_deleted_and_no_legal_resolution(self) -> None:
        self.assertRegex(PAGE, r"Closing a case does not delete it")
        self.assertRegex(PAGE, r"not (a )?(legal )?(determination|resolution)|does not mean")

    def test_workspace_has_close_and_export_actions_using_csrf_and_errors(self) -> None:
        for element_id in ("settlement-case-export", "settlement-case-close"):
            self.assertIn(f'id="{element_id}"', PAGE)
        self.assertIn("/export`", PAGE)
        self.assertIn("/close`", PAGE)
        body = PAGE[PAGE.index("async function downloadCaseExport") :][:1800]
        self.assertIn("csrfHeaders", PAGE)
        self.assertIn("response.status === 401", body)
        self.assertIn("response.blob()", body)
        self.assertIn("aria-live", PAGE)

    def test_close_requires_confirmation_and_reopen_refreshes_dashboard(self) -> None:
        close_fn = PAGE[PAGE.index("async function closeCaseFromWorkspace") :][:1500]
        self.assertIn("confirm(", close_fn)
        self.assertIn("loadDashboardStatus", close_fn)
        reopen_fn = PAGE[PAGE.index("async function reopenClosedCase") :][:1500]
        self.assertIn("loadDashboardStatus", reopen_fn)


if __name__ == "__main__":
    unittest.main()
