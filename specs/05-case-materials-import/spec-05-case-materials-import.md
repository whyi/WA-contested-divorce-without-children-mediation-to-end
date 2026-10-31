# Spec 05: Case-Materials Selection and Import

- **Status:** Draft
- **Related issue:** [#28 — Implement case-materials import page with cloud file pickers](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/28)
- **Related specifications:** [Spec 02: Overall Requirements](../02-requirements/spec-02-overall-requirements.md), [Spec 03: Authentication](../03-authentication/spec-03-authentication.md), [Spec 04: Initial Onboarding](../04-initial-onboarding-empty-state/requirements.md)
- **Objective:** Define the page and user-controlled workflow for adding existing case materials from a device, Google Drive, or Dropbox.
- **Scope:** This specification covers entering the materials flow, selecting and reviewing files, explicit import confirmation, and import feedback. It does not enable production case/document APIs or define document extraction and legal review.

## 1. User Flow

1. An authenticated user with no cases chooses **“I already have case materials, so I'll upload them”** on the onboarding empty state.
2. The application opens a **“Start with your case materials”** page with three ways to add files:
   - Choose files from the user's device, including drag-and-drop.
   - Choose files from Google Drive.
   - Choose files from Dropbox.
3. The user selects one or more files. For a cloud provider, the application obtains authorization only as needed and opens that provider's file picker. Signing in to or connecting a provider does not select or import files.
4. The application displays a review list of the selected files, including filename, file type, and size, with an option to remove each file.
5. The user explicitly confirms **“Import selected files”** before any file contents are uploaded to the application or associated with a case.
6. The application displays per-file progress and the final outcome. The user can retry failed files without reselecting files that imported successfully.
7. Canceling or leaving before confirmation discards the pending selection and does not create a case or import files.

## 2. Page and Selection Requirements

- **FR-05-01 — Entry point:** The onboarding materials action must open this page. The page must provide a clear way to return to the account dashboard.
- **FR-05-02 — Three selection sources:** The page must offer device selection, Google Drive selection, and Dropbox selection as clearly labeled actions.
- **FR-05-03 — Device selection:** Device selection must support multiple files and drag-and-drop. The page must accept PDF and DOCX files, consistent with the currently supported document formats.
- **FR-05-04 — Limits before selection:** Before import, the UI must state supported formats and the configured upload-size limit. The current default maximum is 20 MiB per file (`MAX_UPLOAD_BYTES`); the displayed limit must reflect the active configuration rather than a hard-coded value.
- **FR-05-05 — Cloud file picker:** Each cloud action must open that provider's file picker and allow the user to select specific files. The application must not scan, synchronize, or import an entire account or folder without explicit per-file selection.
- **FR-05-06 — Selection review:** Before import, show the selected-file list with filename, type, and size. Users must be able to remove any selected file. Invalid or unsupported files must be identified with a reason and excluded from import unless corrected or removed.
- **FR-05-07 — Explicit confirmation:** No file content may be transferred to application storage, and no case may be created, merely because the page was opened, a provider account was connected, or files were selected in a picker. Import begins only after the user confirms the reviewed selection.
- **FR-05-08 — Duplicate selection:** If the same file is selected more than once in the pending selection, the UI must avoid duplicate import entries or clearly identify the duplicates before confirmation.

## 3. Import and Case Association

- **FR-05-09 — Authenticated ownership:** Every import must be associated with the authenticated account and a case for which that account has an explicit authorized membership. Authentication alone must never grant access to an existing case.
- **FR-05-10 — New case initialization:** For this onboarding path, initialize a new draft case only when the user confirms a non-empty, valid selection for import. The draft must be associated with the authenticated account under the case-membership policy. Opening the page, selecting files, canceling, or submitting an invalid selection must not create a case.
- **FR-05-11 — Upload validation:** The server must validate file type, size, and content independently of client-provided filename or metadata. It must reject empty, malformed, unsupported, or oversized files with a useful per-file error. Existing PDF page-count limits must be enforced during document processing.
- **FR-05-12 — Partial outcomes:** Report status per file. A failure for one file must not hide successful imports of other files. Retry must target only failed files and must not create duplicate documents for files already imported.
- **FR-05-13 — Safe retries:** Repeated submissions caused by retries or network interruption must not create duplicate cases or documents. The implementation must use an idempotency strategy appropriate to the existing API and persistence model.
- **FR-05-14 — No premature processing claims:** Successful import means the file was accepted and stored. The page must not imply that the document has been legally reviewed, verified, or incorporated into a court filing.

## 4. Cloud Authorization and Data Handling

- **FR-05-15 — User-initiated access:** Request cloud authorization only when the user chooses the corresponding provider. Explain what data will be accessed and that only files selected in the picker will be imported.
- **FR-05-16 — Least privilege:** Request the minimum provider permissions that support selecting and reading user-chosen files. Do not request broad account-wide read/write access when a narrower file-selection permission is available.
- **FR-05-17 — No implicit transfer:** Provider authorization and picker results must not trigger content download or application storage until the user confirms the review list.
- **FR-05-18 — Credential protection:** Provider tokens and file contents must not be exposed in UI text, URLs, analytics, or application logs. Credentials must be handled only as long as needed for the user-authorized operation and protected according to the application's secret-handling policy.
- **FR-05-19 — Cancellation and revocation:** If the user cancels provider authorization or the picker, return to the materials page without importing files. Expired or revoked authorization must produce a clear recovery action, such as reconnecting the provider.
- **FR-05-20 — Provider failure:** Provider outages, unavailable files, and permission errors must be shown as actionable errors without silently treating them as an empty successful selection.

## 5. Loading, Progress, and Error States

- The page must distinguish initial loading, empty selection, ready-to-import, importing, partially complete, complete, and failed states.
- Disable duplicate confirmation while an import request is in progress, while preserving a clear route to cancel where cancellation is safe.
- Show per-file progress or status, and provide actionable validation or transfer errors without exposing tokens, internal paths, or sensitive provider response details.
- If the user's session expires, require sign-in again and do not expose pending case data or continue importing under an unauthenticated context.
- When a request result is uncertain because of a network interruption, reconcile server-side import status before offering a retry to avoid duplicate case or document creation.

## 6. Accessibility and Responsive Behavior

- All source actions, file controls, removal actions, and confirmation controls must be keyboard accessible and have accessible names.
- Drag-and-drop must have an equivalent keyboard-accessible file selection action.
- Announce import progress and per-file completion or failure to assistive technology.
- Errors must identify the affected file and must not rely on color alone.
- The page and review list must remain usable on narrow screens without horizontal scrolling.

## 7. Acceptance Criteria

1. Choosing the materials action from onboarding opens the “Start with your case materials” page.
2. The page offers device selection, Google Drive, and Dropbox.
3. Device selection supports multiple PDF/DOCX files and drag-and-drop, and shows the active per-file size limit before import.
4. Cloud providers open a provider-backed picker; connecting an account alone never imports files.
5. Only user-selected files appear in the review list, and users can inspect and remove them before confirmation.
6. No content is sent to application storage and no case is created before explicit confirmation of a valid selection.
7. Invalid, oversized, empty, or malformed files are rejected server-side and receive actionable per-file feedback.
8. Import progress and success/failure are reported per file; retrying failures does not duplicate successful imports or cases.
9. Imports are associated only with the authenticated account and its explicitly authorized case membership.
10. Provider credentials and document contents are not exposed in UI text, URLs, analytics, or logs.
11. The flow is keyboard accessible, announces status changes, and works on narrow screens.
12. Automated tests cover entry routing, device-file validation, selection review/removal, authorization and picker cancellation, explicit confirmation, partial failure, and idempotent retry behavior. Provider integrations must be testable with mocked provider responses when live credentials are unavailable.

## 8. Out of Scope

- Automatic background synchronization, folder watching, or account-wide import from Google Drive or Dropbox.
- OneDrive or other cloud-storage providers.
- OCR, text extraction, AI review, legal analysis, or determination of document completeness.
- Editing documents, creating court filings, or submitting materials to a court or another party.
- Enabling case/document APIs before authentication, case-membership authorization, storage, and deployment requirements are approved.

## 9. Implementation Constraints and Open Decisions

- The existing application defaults to a 20 MiB upload-size limit and supports PDF and DOCX validation. Implementations must read the configured limit rather than duplicate its default in the UI.
- The existing preview-only onboarding route does not create cases or accept uploads. This specification describes the intended behavior but does not authorize bypassing the existing fail-closed authentication and case-authorization boundaries.
- Google Drive and Dropbox credentials, provider application registration, OAuth callback origins, scopes, token lifecycle, and deployment configuration must be established before enabling live provider access.
- Product and security review must confirm the retention and deletion policy for imported source files before handling real case materials.
- Provider-specific rules for file shortcuts, shared files, unavailable downloads, and export/conversion of provider-native formats must be finalized before supporting those file types. Until then, reject unsupported types clearly.
