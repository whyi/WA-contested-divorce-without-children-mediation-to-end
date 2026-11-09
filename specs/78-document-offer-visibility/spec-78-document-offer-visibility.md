# Spec 78: Document-mode optional offer visibility

## Amendment

This additive specification amends Spec 73's optional-offer layout and save-choice visibility. It preserves the existing saved-offer removal confirmation and document import behavior.

## Requirements

- Place the optional opposing-offer checkbox outside the offer panel, immediately below the import-selected-files action.
- Start with the checkbox unchecked and hide the complete offer panel and `Save offer choice` action when no saved affirmative offer exists.
- Checking the checkbox reveals the offer panel and save-choice action. Unchecking hides both, including their headings, notes, documents, and asset terms.
- A saved affirmative offer restores the checked checkbox and visible panel on reload. Preserve confirmation before removing a saved offer; cancellation or failed removal restores the checked state and visible controls.
- Keep existing offer-source validation and save behavior. This change does not automatically import files or save an affirmative offer.
- Remove the trailing underlined Back link from document mode. Keep only the existing Back button and its discard/deletion confirmation behavior. Preserve wizard and other demo navigation.

## Verification

Browser regressions check unchecked, checked, unchecked-again, saved-offer reload/removal, checkbox placement outside the panel, conditional save-choice visibility, and exactly one document-mode Back control.
