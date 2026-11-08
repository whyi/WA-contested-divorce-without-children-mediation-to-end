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


def _finish_handler() -> str:
    start = PAGE.index('wizardFinish.addEventListener("click"')
    return PAGE[start : PAGE.index("wizardClearButton.addEventListener", start)]


class WizardSaveAndContinueTests(unittest.TestCase):
    def test_finish_saves_creates_attempt_one_then_opens_the_attempt_screen(self) -> None:
        handler = _finish_handler()
        create = _function_body("createWizardAttemptOne")

        self.assertLess(handler.index("saveWizardDraft()"), handler.index("createWizardAttemptOne()"))
        self.assertLess(
            handler.index("createWizardAttemptOne()"), handler.index("window.location.assign(")
        )
        self.assertIn("/wizard-attempt", create)
        self.assertIn('method: "POST"', create)
        self.assertIn('preparationCaseId ? "/"', handler)

    def test_a_failed_creation_keeps_the_user_on_the_wizard_with_a_retry(self) -> None:
        handler = _finish_handler()
        create = _function_body("createWizardAttemptOne")
        catch = create[create.index("catch (error)") :]

        self.assertIn("!(await createWizardAttemptOne())) return;", handler)
        self.assertNotIn("location.assign", catch)
        self.assertIn("wizardFinish.disabled = false", catch)
        self.assertIn("Your draft is saved", catch)
        self.assertIn("return false", catch)
        self.assertIn('"error"', catch)

    def test_demo_wizard_keeps_its_own_destination(self) -> None:
        handler = _finish_handler()

        self.assertIn("demoAssetOverviewUrl(demoCurrentCaseId)", handler)
        self.assertIn("if (preparationCaseId && !(await createWizardAttemptOne()))", handler)

    def test_nothing_else_creates_the_attempt_automatically(self) -> None:
        self.assertEqual(PAGE.count("/wizard-attempt`"), 3)
        for name in ("openActiveCase", "enterSignedInAccount", "loadSettlementWizardAttempt"):
            body = _function_body(name)
            self.assertNotIn('method: "POST"', body, name)
        self.assertNotIn("wizard-intake", _function_body("enterSignedInAccount"))


class WizardAttemptScreenTests(unittest.TestCase):
    def test_panel_and_empty_state_exist_with_the_required_actions(self) -> None:
        self.assertIn("Values from your case information", PAGE)
        self.assertIn('id="settlement-wizard-create"', PAGE)
        self.assertIn("Create Attempt 1 from your case information", PAGE)
        self.assertEqual(PAGE.count('class="settlement-wizard-edit-link"'), 2)
        self.assertIn("do not change an attempt that already exists", PAGE)

    def test_only_wizard_cases_read_the_wizard_attempt(self) -> None:
        body = _function_body("loadSettlementWizardAttempt")

        self.assertLess(
            body.index('settlementCaseWorkflowMode !== "wizard"'), body.index("/wizard-attempt")
        )
        self.assertIn("settlementCaseWorkflowMode = item.workflow_mode", _function_body("openActiveCase"))
        self.assertIn("loadSettlementWizardAttempt(caseId)", _function_body("openSettlementPlanner"))

    def test_entered_amounts_are_formatted_from_integer_cents_without_floats(self) -> None:
        body = _function_body("formatWizardCents")

        self.assertNotIn("toFixed", body)
        self.assertNotIn("/ 100)", body.replace("Math.floor(abs / 100)", ""))
        self.assertIn("abs % 100", body)

    def test_missing_information_hides_scenario_tools_and_lists_the_needs(self) -> None:
        body = _function_body("renderSettlementWizardAttempt")

        self.assertIn("settlementPlannerContent.hidden = true", body)
        self.assertIn("result.needs", body)
        self.assertIn("Your case information is ready.", body)
        self.assertIn("report.included", body)
        self.assertIn("report.excluded", body)

    def test_creating_from_the_empty_state_reopens_the_attempt_workspace(self) -> None:
        body = _function_body("createSettlementWizardAttempt")

        self.assertIn('method: "POST"', body)
        self.assertIn("openSettlementPlanner(caseId)", body)
        self.assertIn("needs_information", body)
        self.assertIn("Try again.", body)


class AttemptCountLabelTests(unittest.TestCase):
    def test_unlimited_attempts_never_render_of_null(self) -> None:
        label = _function_body("settlementAttemptCountLabel")

        self.assertIn("item.attempt_limit == null", label)
        self.assertNotIn("attempt_limit} —", PAGE)
        self.assertNotIn("of ${selectedItem.attempt_limit}", PAGE)
        self.assertNotIn("of ${item.attempt_limit}", PAGE.replace(label, ""))


if __name__ == "__main__":
    unittest.main()
