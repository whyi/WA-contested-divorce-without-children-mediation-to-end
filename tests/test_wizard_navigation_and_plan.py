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


class WizardBackAndContinueTests(unittest.TestCase):
    def test_back_opens_the_start_path_choice_instead_of_the_account_page(self) -> None:
        preparation = _function_body("showPreparation")
        self.assertIn('backLink.textContent = "Back"', preparation)
        self.assertNotIn("view=account", preparation)
        self.assertIn("openStartPathDialog();", PAGE)
        self.assertIn('id="start-path-dialog"', PAGE)
        self.assertEqual(PAGE.count('data-path-mode="'), 2)
        self.assertIn('id="start-path-cancel"', PAGE)

    def test_choosing_a_path_updates_the_case_then_opens_that_path(self) -> None:
        body = _function_body("chooseStartPath")

        self.assertIn("if (mode === preparationMode)", body)
        self.assertLess(
            body.index("/workflow-mode"),
            body.index("window.location.assign("),
        )
        self.assertIn('method: "PUT"', body)
        self.assertIn("startPathStatus.textContent = error instanceof Error", body)

    def test_real_wizard_hides_the_demo_only_asset_overview_link(self) -> None:
        preparation = _function_body("showPreparation")

        self.assertIn('document.getElementById("demo-wizard-back").parentElement.hidden = true', preparation)

    def test_finish_saves_then_continues_to_the_case_entry(self) -> None:
        self.assertIn('wizardFinish.textContent = "Save and continue";', PAGE)
        handler = PAGE.split('wizardFinish.addEventListener("click", async () =>', 1)[1].split(
            "wizardClearButton.addEventListener", 1
        )[0]
        self.assertLess(handler.index("await saveWizardDraft()"), handler.index("window.location.assign("))
        self.assertIn('preparationCaseId ? "/" : demoAssetOverviewUrl', handler)
        self.assertIn('id="wizard-finish-hint"', PAGE)

    def test_entry_opens_attempts_regardless_of_wizard_completeness(self) -> None:
        entry = _function_body("openActiveCase")
        self.assertNotIn("wizardIntakeComplete", PAGE)
        self.assertNotIn("window.location", entry)
        self.assertIn("await openSettlementPlanner(item.id)", entry)
        self.assertIn("settlementEditIntake.hidden = !startUrl", entry)
        self.assertIn("settlementEditIntake.href = startUrl", entry)
        self.assertRegex(PAGE, r'id="settlement-edit-intake" href="#" hidden>Edit case information</a>')


class SignedInHomeTests(unittest.TestCase):
    def test_logo_opens_the_home_page_for_signed_in_users(self) -> None:
        self.assertIn('id="brand-link" href="/" aria-label="Casework home"', PAGE)
        status = _function_body("loadDashboardStatus")
        self.assertIn('brandLink.href = "/?view=home"', status)
        self.assertLess(status.index("else if (homeMode)"), status.index("await enterSignedInAccount(account)"))
        self.assertIn('new URLSearchParams(window.location.search).get("view") === "home"', PAGE)

    def test_home_page_leads_signed_in_users_to_their_case(self) -> None:
        body = _function_body("showSignedInHome")

        self.assertIn("showPublicPage();", body)
        for control in ('"account-entry"', '"hero-primary-action"', '"closing-account-cta"'):
            self.assertIn(control, body)
        self.assertIn('link.href = "/"', body)
        self.assertIn('document.getElementById("account").hidden = true', body)
        self.assertIn("accountToolsLink.hidden = false", body)


class AccountPlanCardTests(unittest.TestCase):
    def test_plan_card_is_a_labelled_region_in_the_account_area(self) -> None:
        match = re.search(
            r'<section class="account-tools" id="account-tools".*?<section class="plan-card" id="plan-card" aria-labelledby="plan-name">(.*?)</section>\s*<section class="closed-cases"',
            PAGE,
            re.S,
        )
        self.assertIsNotNone(match)
        card = match.group(1)
        self.assertIn('id="plan-name"', card)
        self.assertRegex(card, r'id="plan-summary" role="status" aria-live="polite"')
        self.assertRegex(card, r'id="plan-action"[^>]*aria-expanded="false" aria-controls="plan-packages" hidden>Upgrade</button>')

    def test_plan_card_reflects_server_entitlement_and_offers_no_downgrade(self) -> None:
        body = _function_body("loadPlanCard")

        self.assertIn("/api/billing/account/entitlement", body)
        self.assertIn("/api/billing/packages", body)
        self.assertIn('entitlement.status === "paid"', body)
        self.assertIn('"Paid plan" : "Free plan"', body)
        self.assertIn('"Buy more credits" : "Upgrade"', body)
        lowered = PAGE.casefold()
        self.assertNotIn("downgrade-to-free", lowered)
        self.assertNotIn("switch to free", lowered)

    def test_upgrade_lists_server_packages_and_uses_the_existing_checkout(self) -> None:
        toggle = _function_body("togglePlanPackages")
        self.assertIn("planPackageData", toggle)
        self.assertIn("Create your case first", toggle)
        self.assertIn("not available yet", toggle)
        self.assertIn("button.disabled = !pack.available", toggle)

        checkout = _function_body("startAccountCreditCheckout")
        self.assertIn("/api/billing/cases/${planCaseId}/checkout", checkout)
        self.assertIn('checkout.hostname !== "checkout.stripe.com"', checkout)
        self.assertIn("showSignIn(", checkout)

    def test_account_area_loads_the_plan_when_shown(self) -> None:
        self.assertIn("void loadPlanCard();", _function_body("showAccountTools"))
        self.assertIn("planCaseId = account.cases[0]?.id ?? null", _function_body("enterSignedInAccount"))
        self.assertIn('planAction.addEventListener("click", togglePlanPackages)', PAGE)


if __name__ == "__main__":
    unittest.main()
