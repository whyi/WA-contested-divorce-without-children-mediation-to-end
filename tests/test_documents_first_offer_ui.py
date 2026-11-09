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


class DocumentsFirstScreenTests(unittest.TestCase):
    def test_documents_use_the_shared_demo_template(self) -> None:
        initialize = _function_body("initializeCaseDocumentsLayout")
        self.assertIn('cloneCaseTemplate(document.getElementById("documents-demo")', initialize)
        self.assertIn('textContent = "I have all documents"', initialize)
        self.assertIn('id="demo-file-input"', PAGE)
        self.assertIn('id="demo-files-next"', PAGE)
        self.assertIn('id="demo-documents-back"', PAGE)

    def test_the_previous_page_is_deleted_not_hidden(self) -> None:
        for element_id in ("materials-workflow", "materials-file-input", "materials-import",
                           "materials-back", "analysis-controls", "proposal-review",
                           "existing-offer-toggle", "existing-offer-continue"):
            self.assertNotIn(f'id="{element_id}"', PAGE)
        self.assertNotIn("Start with your case materials", PAGE)
        self.assertNotIn("function continueFromDocuments", PAGE)
        self.assertNotIn("function openAssetAnalysis", PAGE)

    def test_selection_does_not_import_and_next_is_explicit(self) -> None:
        render = _function_body("renderCaseSelectedDocuments")
        self.assertNotIn("fetch(", render)
        self.assertNotIn("uploadCaseFiles(", render)
        self.assertIn("!caseSelectedDocuments.length", render)
        self.assertIn("caseOfferLoading || caseOfferLoadFailed || caseOfferBusy", render)
        initialize = _function_body("initializeCaseDocumentsLayout")
        self.assertIn("await uploadCaseFiles(caseSelectedDocuments)", initialize)
        self.assertIn("no AI analysis starts automatically", initialize)
        self.assertIn("window.location.assign(`/case/assets?case_id=", initialize)

    def test_retry_preserves_identity_and_quota_checks_all_pending_files(self) -> None:
        upload = _function_body("uploadCaseFiles")
        self.assertIn("caseImportIdentities.get(file)", upload)
        self.assertIn("identity.attempted", upload)
        self.assertIn("identity.batch", upload)
        self.assertIn("identity.documentId", upload)
        self.assertIn("config.attachment_count + pending.length > config.max_attachments", upload)
        self.assertIn("file.size > config.max_upload_bytes", upload)

    def test_back_opens_the_start_path_choice_without_deletion(self) -> None:
        initialize = _function_body("initializeCaseDocumentsLayout")
        self.assertIn('window.location.assign("/?start_path=1")', initialize)
        self.assertNotIn("DELETE", initialize)
        self.assertNotIn("view=account", initialize)

    def test_wizard_offer_details_remain_optional_and_independent(self) -> None:
        preparation = _function_body("showPreparation")
        self.assertIn("wizardDemoPage.hidden = false", preparation)
        self.assertIn("preparationView.append(wizardDemoPage)", preparation)
        self.assertIn('.querySelector(".demo-flow-panel > .demo-flow-actions").before(existingOfferPanel)', preparation)
        self.assertNotIn("function applyExistingOfferGate", PAGE)
        self.assertIn('<legend>Has the other party already made an offer?</legend>', PAGE)


class DocumentsCaseDialogTests(unittest.TestCase):
    def test_documents_path_creates_the_case_without_the_offer_question(self) -> None:
        create = _function_body("createCaseFromDashboard")
        self.assertIn("createCaseFromDashboard(button.dataset.startMode, button)", PAGE)
        self.assertNotIn("Create case and continue to documents", PAGE)
        self.assertNotIn("Create your case, then upload your documents right away.", PAGE)
        self.assertIn("workflow_mode: mode", create)
        self.assertNotIn("existing_offer", create)
        self.assertIn("/onboarding/${mode}?case_id=", create)
        self.assertIn("if (button.disabled) return;", create)

    def test_wizard_path_has_no_creation_interstitial(self) -> None:
        self.assertNotIn('id="case-create-offer-intake"', PAGE)
        self.assertNotIn('id="case-offer-question"', PAGE)
        self.assertNotIn("Before starting the guided path", PAGE)
        self.assertNotIn("Create case and start the wizard", PAGE)


if __name__ == "__main__":
    unittest.main()
