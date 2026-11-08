# Spec 75: Direct Documents Entry

- **Status:** Specified; implementation and regression tests in the same pull request
- **Amends:** [Spec 73](../73-documents-first-upload-and-optional-offer/spec-73-documents-first-upload-and-optional-offer.md), FR-73-07 and acceptance criterion 6. Existing specifications remain unchanged.
- **Objective:** Remove the redundant documents-path case-creation confirmation.

## Requirements

1. Clicking **I have documents** in the real-account start choice creates the case and navigates directly to **Start with your case materials** (`/onboarding/upload?case_id=...`). No second click or confirmation screen is required.
2. Remove the documents-only intermediate screen logic and its **Create case and continue to documents** action from the repository. Keep the wizard's existing offer intake and confirmation unchanged.
3. Preserve the optional case label, create the case in upload mode without an offer answer, and preserve the documents screen's optional offer checkbox.
4. While creation is pending, disable both start choices and cancellation to prevent duplicate requests or switching workflows mid-request.
5. A creation failure stays on the start choice, displays an actionable error, and permits retry. Do not navigate or display success on failure.
6. Demo navigation and file-selection behavior remain unchanged.

## Verification

- Browser regressions assert that one click opens the materials heading and enabled file picker, with one creation request and no existing-offer submission.
- Browser regressions cover pending creation, failure/retry, the optional case label, and the unchanged wizard offer gate.
- Static tests assert that the removed screen's text is absent from the application.
