import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class DemoEntryRegressionTests(unittest.TestCase):
    def test_upload_and_demo_pages_remain_available_without_workspace_remnants(self) -> None:
        with patch("app.main.require_current_user"), TestClient(app, follow_redirects=False) as client:
            for path in (
                "/onboarding/upload?case_id=synthetic",
                "/demo/documents?source=demo1&demo_case_id=synthetic",
                "/demo/wizard?source=demo2&demo_case_id=synthetic",
                "/demo/files?source=demo1&demo_case_id=synthetic",
            ):
                with self.subTest(path=path):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertNotIn('id="materials-workflow"', response.text)
                    self.assertIn('id="documents-demo"', response.text)
                    self.assertIn('id="wizard-demo"', response.text)
                    self.assertIn('id="demo-file-manager"', response.text)
                    self.assertNotIn("Your case workspace", response.text)

    def test_legacy_entries_always_redirect_to_the_matching_start_choice(self) -> None:
        legacy_entries = {
            "/demo": "/demo/start?source=demo2",
            "/demo?source=demo1": "/demo/start?source=demo1",
            "/demo?source=demo2": "/demo/start?source=demo2",
            "/demo/1": "/demo/start?source=demo1",
            "/demo/1/dashboard": "/demo/start?source=demo1",
            "/demo/2": "/demo/start?source=demo2",
            "/demo/2/dashboard": "/demo/start?source=demo2",
            "/demo/dashboard": "/demo/start?source=demo2",
        }

        with TestClient(app, follow_redirects=False) as client:
            for path, target in legacy_entries.items():
                with self.subTest(path=path):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 307)
                    self.assertEqual(response.headers["location"], target)

    def test_case_overview_requires_a_case_id_and_accepts_both_demo_plans(self) -> None:
        with TestClient(app, follow_redirects=False) as client:
            for source in ("demo1", "demo2"):
                with self.subTest(source=source):
                    start_response = client.get(f"/demo/start?source={source}")
                    self.assertEqual(start_response.status_code, 200)

                    no_case_response = client.get(f"/demo?source={source}")
                    self.assertEqual(no_case_response.status_code, 307)
                    self.assertEqual(
                        no_case_response.headers["location"],
                        f"/demo/start?source={source}",
                    )

                    existing_case_response = client.get(
                        f"/demo?source={source}&demo_case_id=case-{source}"
                    )
                    self.assertEqual(existing_case_response.status_code, 200)

            for path in ("/demo/start?source=invalid", "/demo?source=invalid"):
                with self.subTest(path=path):
                    self.assertEqual(client.get(path).status_code, 400)

    def test_each_demo_start_page_opens_the_choice_without_rendering_case_lists(self) -> None:
        with TestClient(app) as client:
            for source in ("demo1", "demo2"):
                with self.subTest(source=source):
                    response = client.get(f"/demo/start?source={source}")
                    self.assertEqual(response.status_code, 200)
                    page = response.text
                    start_branch = page.rsplit("} else if (demoStartMode) {", 1)[1].split(
                        "} else if (demoMode)", 1
                    )[0]

                    self.assertIn('document.body.dataset.demoPage = "start"', start_branch)
                    self.assertIn('id="demo-workspace-header" hidden', page)
                    self.assertIn("showDemoCaseChoicePage()", start_branch)
                    self.assertNotIn("renderCases(", start_branch)
                    self.assertIn(
                        'id="existing-cases" hidden',
                        page,
                    )
                    self.assertIn(
                        'body[data-demo-page="start"] main > section:not(#account-dashboard)',
                        page,
                    )
                    self.assertNotIn('id="demo-my-cases-link"', page)
                    self.assertNotIn('id="demo-inactive-cases"', page)
                    self.assertNotIn("Archived cases", page)
                    self.assertIn('function showDemoCaseChoicePage()', page)
                    self.assertIn("demoCaseChoicePage.hidden = false", page)

    def test_both_start_choices_share_one_new_id_and_keep_the_selected_plan(self) -> None:
        with TestClient(app) as client:
            for source in ("demo1", "demo2"):
                with self.subTest(source=source):
                    page = client.get(f"/demo/start?source={source}").text
                    self.assertIn(
                        'const demoSource = demoQuery.get("source") === "demo1" ? "demo1" : "demo2"',
                        page,
                    )
                    self.assertIn(
                        'const demoAttemptLimit = demoSource === "demo1" ? 1 : 3;',
                        page,
                    )
                    choice = page.split(
                        "function showDemoCaseChoicePage()", 1
                    )[1].split("\n        }", 1)[0]
                    self.assertEqual(choice.count('createLocalId("case")'), 1)
                    self.assertIn("id: `demo-${createLocalId(\"case\")}`", choice)
                    self.assertIn("const query = `source=${demoSource}&demo_case_id=${encodeURIComponent(pendingDemoCase.id)}`", choice)
                    self.assertIn(
                        'demoCaseDocumentsLink.href = `/demo/documents?${query}`',
                        choice,
                    )
                    self.assertIn(
                        'demoCaseWizardLink.href = `/demo/wizard?${query}`',
                        choice,
                    )
                    self.assertIn('demoCaseChoicePage.hidden = false', choice)

                    start_case = page.split("function startDemoCase(mode, event)", 1)[1].split(
                        "\n        }", 1
                    )[0]
                    self.assertIn('["documents", "wizard"].includes(mode)', start_case)
                    self.assertIn("saveDemoCaseData({", start_case)
                    self.assertIn('workflow_mode: mode === "documents" ? "upload" : "wizard"', start_case)
                    self.assertIn("pendingDemoCase.id", start_case)
                    self.assertIn(
                        "`${path}?source=${demoSource}&demo_case_id=${encodeURIComponent(pendingDemoCase.id)}`",
                        start_case,
                    )

    def test_returning_to_start_reopens_the_same_case_instead_of_a_case_dashboard(self) -> None:
        with TestClient(app) as client:
            for source in ("demo1", "demo2"):
                with self.subTest(source=source):
                    page = client.get(f"/demo/start?source={source}").text
                    self.assertIn(
                        "const demoCaseStorageKey = `casework-demo-case-v2:${demoSource}`",
                        page,
                    )
                    self.assertIn(
                        "if (demoCaseData) {\n"
                        "            window.location.replace(demoAssetOverviewUrl(demoCaseData.id));\n"
                        "          } else {\n"
                        "            showDemoCaseChoicePage();",
                        page,
                    )
                    choice = page.split(
                        "function showDemoCaseChoicePage()", 1
                    )[1].split("\n        }", 1)[0]
                    self.assertIn("demoCaseData || loadDemoCaseData()", choice)
                    self.assertIn(
                        "window.location.replace(demoAssetOverviewUrl(existingCase.id))",
                        choice,
                    )
                    self.assertIn("demoCaseChoicePage.hidden = false", choice)

    def test_case_id_and_source_survive_every_demo_case_subpage_return_path(self) -> None:
        case_id = "regression-case-123"
        for source in ("demo1", "demo2"):
            query = f"source={source}&demo_case_id={case_id}"
            with self.subTest(source=source), TestClient(app) as client:
                pages = {
                    path: client.get(f"{path}?{query}").text
                    for path in (
                        "/demo/documents",
                        "/demo/wizard",
                        "/demo/files",
                        "/demo/settlement-completion",
                    )
                }
                for path, page in pages.items():
                    self.assertIn(
                        'const demoCurrentCaseId = demoQuery.get("demo_case_id") || ""',
                        page,
                        msg=path,
                    )
                    self.assertIn(
                        "function demoAssetOverviewUrl(caseId = demoCurrentCaseId)",
                        page,
                        msg=path,
                    )

                self.assertIn("demoCurrentCaseId", pages["/demo/documents"])
                self.assertIn("`demo:${demoSource}:${demoCurrentCaseId}`", pages["/demo/wizard"])
                self.assertIn("demoCaseFilesCaseId = demoCurrentCaseId", pages["/demo/files"])
                self.assertIn("demoFileManagementLink.href =", pages["/demo/files"])
                self.assertIn(
                    "if (demoCurrentCaseId) link.href = demoAssetOverviewUrl()",
                    pages["/demo/wizard"],
                )
                self.assertIn(
                    'window.location.assign(demoAssetOverviewUrl(demoCurrentCaseId))',
                    pages["/demo/documents"],
                )
                self.assertIn(
                    'window.location.assign(demoAssetOverviewUrl(demoCurrentCaseId))',
                    pages["/demo/wizard"],
                )
                self.assertNotIn("settlementCompletionBackToMediation", pages["/demo/settlement-completion"])
                self.assertIn("settlementCompletionBackToCases.href", pages["/demo/settlement-completion"])


if __name__ == "__main__":
    unittest.main()
