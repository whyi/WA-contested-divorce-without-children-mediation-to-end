import re
import unittest
from pathlib import Path

PAGE = (Path(__file__).parents[1] / "src" / "app" / "static" / "index.html").read_text()


class ClosedCaseDashboardTests(unittest.TestCase):
    def test_dashboard_lists_closed_cases_with_accessible_reopen_and_export(self) -> None:
        self.assertRegex(PAGE, r'<div[^>]*id="closed-cases"[^>]*>')
        self.assertIn('<dt id="closed-cases-title">Your case</dt>', PAGE)
        self.assertIn('id="closed-cases-status"', PAGE)
        self.assertRegex(PAGE, r'id="closed-cases-status"[^>]*role="status"[^>]*aria-live="polite"')
        self.assertIn("/api/v1/closed-cases", PAGE)
        self.assertIn("/reopen", PAGE)
        self.assertIn("Reopen your case", PAGE)
        self.assertIn("Export all case data", PAGE)

    def test_closed_case_copy_says_nothing_is_deleted_and_no_legal_resolution(self) -> None:
        self.assertRegex(PAGE, r"Closing a case does not delete it")
        self.assertRegex(PAGE, r"not (a )?(legal )?(determination|resolution)|does not mean")

    def test_workspace_has_close_and_export_actions_using_csrf_and_errors(self) -> None:
        for element_id in ("account-active-case-list",):
            self.assertIn(f'id="{element_id}"', PAGE)
        self.assertIn('close.id = "settlement-case-close"', PAGE)
        self.assertIn("actions.append(exportButton, close, go)", PAGE)
        self.assertIn("/export`", PAGE)
        self.assertIn("void downloadCaseExport(item.id, accountActiveCaseStatus, exportButton)", PAGE)
        self.assertIn("/close`", PAGE)
        body = PAGE[PAGE.index("async function downloadCaseExport") :][:1800]
        self.assertIn("csrfHeaders", PAGE)
        self.assertIn("response.status === 401", body)
        self.assertIn("response.blob()", body)
        self.assertIn("aria-live", PAGE)

    def test_close_requires_confirmation_and_reopen_refreshes_dashboard(self) -> None:
        close_fn = PAGE[PAGE.index("async function closeCaseFromWorkspace") :][:1500]
        self.assertIn("await confirmCaseClosure()", close_fn)
        self.assertIn("loadDashboardStatus", close_fn)
        reopen_fn = PAGE[PAGE.index("async function reopenClosedCase") :][:1500]
        self.assertIn("loadDashboardStatus", reopen_fn)

    def test_permanent_deletion_retains_material_and_account_controls_not_case_button(self) -> None:
        for element_id in (
            "account-permanent-deletion-form",
            "account-permanent-delete-submit",
        ):
            self.assertIn(f'id="{element_id}"', PAGE)
        self.assertIn('Type DELETE MY ACCOUNT', PAGE)
        self.assertNotIn("settlement-case-delete", PAGE)
        self.assertNotIn("active-case-management", PAGE)
        self.assertIn('Permanently delete this saved file? This cannot be undone.', PAGE)
        self.assertIn('confirmation: "DELETE MATERIAL"', PAGE)
        self.assertIn("/permanent-deletion`", PAGE)
        self.assertIn("/materials/${encodeURIComponent(file.id)}/permanent-deletion", PAGE)
        self.assertIn("Provider-managed database backups and snapshots are not configured", PAGE)


if __name__ == "__main__":
    unittest.main()
