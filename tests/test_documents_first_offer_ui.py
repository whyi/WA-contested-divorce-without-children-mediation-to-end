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
    def test_upload_is_visible_as_soon_as_the_documents_screen_loads(self) -> None:
        preparation = _function_body("showPreparation")

        self.assertIn("materialsWorkflow.hidden = !isUpload;", preparation)
        self.assertNotIn("Boolean(preparationCaseId)", preparation)
        gate = _function_body("applyExistingOfferGate")
        self.assertNotIn("materialsWorkflow", gate)

    def test_offer_is_a_checkbox_below_the_upload_and_the_radio_question_is_hidden(self) -> None:
        preparation = _function_body("showPreparation")

        self.assertIn('id="existing-offer-toggle"', PAGE)
        self.assertIn("The other party has already made an offer", PAGE)
        self.assertIn('id="offer-optional-slot"', PAGE)
        self.assertLess(
            PAGE.index('id="materials-status-retry"'), PAGE.index('id="offer-optional-slot"')
        )
        self.assertIn('getElementById("offer-optional-slot").append(existingOfferPanel)', preparation)
        self.assertIn('getElementById("existing-offer-question").hidden = true', preparation)
        self.assertRegex(PAGE, r'<input type="checkbox" id="existing-offer-toggle">')
        self.assertNotRegex(PAGE, r'id="existing-offer-toggle"[^>]*\bchecked\b')

    def test_unchecked_enables_continue_and_checked_requires_saved_details(self) -> None:
        controls = _function_body("updateExistingOfferUploadControls")

        self.assertIn("existingOfferDetails.hidden = !checked", controls)
        self.assertIn("existingOfferSaved?.exists === true && existingOfferSaved.hasDetails", controls)
        self.assertIn("Save offer notes or an offer document before saving this choice.", controls)
        self.assertIn("existingOfferContinue.disabled = !ready", controls)
        self.assertIn('role="status" aria-live="polite"', PAGE[PAGE.index("existing-offer-continue-status") - 80 :][:200])

    def test_offer_choice_is_saved_without_opening_a_deleted_page(self) -> None:
        body = _function_body("continueFromDocuments")

        self.assertIn("existingOfferSaved?.exists !== false", body)
        self.assertIn("await saveExistingOffer()", body)
        self.assertNotIn("window.location", body)
        self.assertIn("Your offer choice is saved.", body)
        self.assertIn("if (existingOfferSaved?.exists !== false) return;", body)

    def test_unchecking_a_saved_offer_confirms_removal_and_keeps_it_if_declined(self) -> None:
        body = _function_body("handleExistingOfferToggle")

        self.assertIn("window.confirm(", body)
        self.assertIn("will no longer be attached", body)
        self.assertIn("existingOfferToggle.checked = true", body)
        self.assertLess(body.index("window.confirm("), body.index("await saveExistingOffer()"))
        self.assertIn('setExistingOfferAnswer("no")', body)

    def test_saved_state_on_the_server_drives_the_checkbox_after_reload(self) -> None:
        render = _function_body("renderExistingOffer")
        load = _function_body("loadExistingOffer")

        self.assertIn('existingOfferToggle.checked = answer === "yes"', render)
        self.assertIn("captureExistingOfferSaved()", load)
        self.assertLess(load.index("captureExistingOfferSaved()"), load.index("restoreExistingOfferRecovery()"))
        self.assertIn('offerGateMode !== "upload"', load)

    def test_refreshing_documents_keeps_the_users_checkbox_choice(self) -> None:
        self.assertIn("loadExistingOffer({ keepToggle: true })", PAGE)
        self.assertIn("if (keepToggle) answer =", _function_body("renderExistingOffer"))

    def test_failed_saves_do_not_navigate(self) -> None:
        body = _function_body("continueFromDocuments")

        self.assertNotIn("window.location", body)
        self.assertIn("finally", body)

    def test_hidden_upload_only_controls_stay_hidden_despite_flex_styles(self) -> None:
        for selector in (
            "#existing-offer-toggle-label[hidden]",
            "#existing-offer-continue-row[hidden]",
            "#existing-offer-save[hidden]",
        ):
            self.assertRegex(PAGE, re.escape(selector) + r"[^{]*\{ display:none; \}")

    def test_the_wizard_path_keeps_its_offer_gate_and_radio_question(self) -> None:
        gate = _function_body("applyExistingOfferGate")

        self.assertIn('offerGateMode === "wizard"', gate)
        self.assertIn("wizardDemoPage.hidden = !open", gate)
        self.assertIn('<legend>Has the other party already made an offer?</legend>', PAGE)
        self.assertIn("return;", _function_body("updateExistingOfferUploadControls"))


class DocumentsCaseDialogTests(unittest.TestCase):
    def test_documents_path_creates_the_case_without_the_offer_question(self) -> None:
        path = _function_body("showCaseStartPath")
        create = _function_body("createCaseFromDashboard")
        documents = _function_body("createDocumentsCase")

        upload = path.split('if (mode === "upload") {', 1)[1].split("return;", 1)[0]
        self.assertIn("caseCreateChoice.hidden = false", upload)
        self.assertIn("caseCreateOfferIntake.hidden = true", upload)
        self.assertIn('createCaseFromDashboard("upload", button)', PAGE)
        self.assertNotIn("Create case and continue to documents", PAGE)
        self.assertNotIn("Create your case, then upload your documents right away.", PAGE)
        self.assertLess(create.index('mode === "upload"'), create.index("case-existing-offer"))
        self.assertIn('workflow_mode: "upload"', documents)
        self.assertNotIn("existing_offer", documents)
        self.assertIn("/onboarding/upload?case_id=", documents)
        self.assertIn("if (button.disabled) return;", documents)

    def test_wizard_path_still_asks_the_offer_question(self) -> None:
        path = _function_body("showCaseStartPath")

        self.assertIn("Before starting the guided path, tell us whether the other party has already made an offer.", path)
        self.assertIn("existing_offer", _function_body("createCaseFromDashboard"))


if __name__ == "__main__":
    unittest.main()
