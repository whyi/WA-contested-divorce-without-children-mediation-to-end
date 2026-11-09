import re
import unittest
from pathlib import Path

PAGE = (Path(__file__).parents[1] / "src" / "app" / "static" / "index.html").read_text(
    encoding="utf-8"
)


class CustomDialogTests(unittest.TestCase):
    def test_application_does_not_use_native_browser_dialogs(self) -> None:
        self.assertIsNone(re.search(r"\bwindow\.(?:alert|confirm|prompt)\s*\(", PAGE))

    def test_shared_dialog_is_styled_accessible_and_supports_all_dialog_actions(self) -> None:
        self.assertIn(
            '<dialog class="app-dialog" id="app-dialog" aria-labelledby="app-dialog-title" aria-describedby="app-dialog-description">',
            PAGE,
        )
        self.assertIn('id="app-dialog-status" role="status" aria-live="polite"', PAGE)
        self.assertIn("function showAppConfirm(", PAGE)
        self.assertIn("function showAppPhraseConfirmation(", PAGE)
        self.assertIn("function showAppNotice(", PAGE)
        self.assertIn("navigator.clipboard.writeText(appDialogCopyText.value)", PAGE)
        self.assertIn("appDialogCopyText.select()", PAGE)
        self.assertIn("appDialogInput.value !== activeAppDialog.options.confirmationPhrase", PAGE)

    def test_all_destructive_confirmations_use_the_shared_custom_dialog(self) -> None:
        self.assertIn("Confirm proposal delivery", PAGE)
        self.assertIn('"DELETE CASE"', PAGE)
        self.assertIn("Type ${options.confirmationPhrase} exactly to continue", PAGE)
        self.assertIn("Permanently delete your account?", PAGE)
        self.assertIn('title: "File already exists"', PAGE)
        self.assertIn('title: "Delete saved file?"', PAGE)


if __name__ == "__main__":
    unittest.main()
