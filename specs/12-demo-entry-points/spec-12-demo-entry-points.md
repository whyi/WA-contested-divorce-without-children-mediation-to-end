# Spec 12: Demo Entry Points

- **Status:** Draft
- **Related issue:** [#53 — Add document-upload and mediation wizard demo entry points](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/53)
- **Related specifications:** [Spec 04: Initial Onboarding Empty-State Dashboard and Dual-Path Routing](../04-initial-onboarding-empty-state/requirements.md), [Spec 10: Mock Asset-Analysis Dashboard](../10-mock-asset-analysis-dashboard/spec-10-mock-asset-analysis-dashboard.md)
- **Objective:** Offer three clearly distinguished ways to preview the product: the existing analysis demo, a local-only document-selection demo, and a single-page mediation intake wizard demo.
- **Scope:** Public demo entry-point labels and navigation, local file selection that never uploads, and a local-only wizard preview with a filed-case eligibility gate. Existing authenticated onboarding, upload, wizard, and analysis behavior is unchanged.

## 1. Demo Entry Choices

- **FR-12-01 — Three choices:** On the public landing page, show three clearly named demo actions:
  1. **Existing demo**
  2. **I have all documents demo**
  3. **Wizard demo**
- **FR-12-02 — Existing demo continuity:** Rename every current user-facing **Demo** link that opens `/demo` to **Existing demo**, including the landing-page navigation and sign-in footnote. These links continue to open the existing fictional asset-analysis preview without authentication, upload, or case lookup.
- **FR-12-03 — Clear distinction:** Explain briefly that the document-selection demo previews the materials path, the wizard demo previews guided intake, and Existing demo opens sample analysis results. Do not imply that either new demo creates a case or analyzes user data.
- **FR-12-04 — Existing authenticated actions:** Do not rename or change the authenticated account's existing **I already have case materials, so I'll upload them** and **Guide me through the wizard step by step** actions.

## 2. Document-Selection Demo

- **FR-12-05 — Local file chooser:** **I have all documents demo** opens a distinct demo-only materials-selection view. The user can choose one or more local files using the browser file picker and review the selected file names before continuing.
- **FR-12-05a — Supported file types:** Match the existing materials workflow's supported file types (PDF and DOCX). Reject unsupported types with an inline explanation without reading or uploading file contents.
- **FR-12-06 — No upload or file reading:** This view does not upload, transmit, parse, hash, persist, or otherwise read selected file contents. Selecting files is only a local browser interaction. Do not create an import batch, case, or upload request.
- **FR-12-07 — Selection management:** Let the user remove selected files and select replacements or additional files. Clearly state that files stay on the device and are used only to preview the flow.
- **FR-12-08 — Continue to Existing demo:** Provide a **Next** action. It is enabled after at least one file is selected. Activating it navigates to the existing `/demo` preview; selected files and their names are not passed to that page or persisted.
- **FR-12-09 — Return navigation:** Provide a way to return to the landing page from the document-selection demo without starting an upload.

## 3. Single-Page Wizard Demo

- **FR-12-10 — One-page layout:** **Wizard demo** opens one vertically ordered questionnaire page. Do not require navigation between separate question pages. Use clear headings and grouping to make the sequence understandable.
- **FR-12-11 — First question and gate:** The first question asks whether the divorce case has been filed, with **Yes** and **No** choices. No later question or completion action is available until **Yes** is selected.
- **FR-12-12 — Blocking explanation:** Selecting **No** opens a blocking dialog explaining that this demo assumes the case has been filed and has reached the mediation stage; a case that has not been filed cannot continue through this workflow. The dialog must not be dismissible by clicking outside it. A clear acknowledgement/close action may dismiss the dialog, but the remaining questions and completion action remain disabled until the answer changes to **Yes**.
- **FR-12-13 — Filed-state change:** If the user changes the answer from **Yes** to **No** after entering other answers, immediately block the remaining form and completion action and show the same explanation. Do not erase the other answers merely because the gate is temporarily closed.
- **FR-12-14 — Party role:** After the filed-case question, ask whether the user is the **Petitioner** or **Respondent**. Require one selection before enabling completion.
- **FR-12-15 — Completion:** When **Yes** is selected and a party role is chosen, enable **Finish demo**. Activating it shows a local-only completion confirmation that clearly says answers were not submitted or saved. The confirmation may offer a separate **Existing demo** link to `/demo`; do not attach, transmit, or persist questionnaire answers.
- **FR-12-16 — Demo-only answers:** The wizard does not create or update a case, submit a legal form, call an AI provider, or save answers to an API, database, or browser storage.
- **FR-12-17 — No legal conclusion:** The filed-case gate is workflow eligibility guidance only. Do not provide legal advice or imply that passing the gate confirms a user's legal status or eligibility for mediation.
- **FR-12-18 — Return navigation:** Provide a way to return to the landing page without submitting answers.

## 4. Accessibility and Responsive Behavior

- **FR-12-19 — Keyboard and assistive technology:** All three entry choices, the file picker, selected-file removal, wizard controls, and navigation are keyboard-operable with descriptive accessible names. Use a semantic dialog with an accessible title and description, focus management, and an explicit acknowledgement action. Announce relevant validation and selection status.
- **FR-12-20 — Narrow screens:** Keep all entry choices, file names/actions, wizard questions, and the blocking dialog usable on narrow screens without horizontal scrolling.
- **FR-12-21 — Reduced motion:** Do not require animation to understand navigation or the blocking state; respect reduced-motion preferences.

## 5. Acceptance Criteria

1. The public landing page offers the three exact demo labels, and **Existing demo** still opens the current `/demo` analysis preview.
2. The authenticated onboarding actions retain their existing labels and behavior.
3. The document-selection demo permits local file selection and removal, makes no upload or analysis request, and **Next** opens `/demo` only after at least one file is selected.
4. No selected file or file name is sent to `/demo`, an API, or browser storage.
5. The wizard is one page with the filed-case question first and the petitioner/respondent question directly after it.
6. With **No** selected, a blocking, accessible dialog explains the filed-case mediation assumption; later questions and completion remain unavailable after the dialog is acknowledged.
7. With **Yes** selected but no party role, completion remains disabled. With **Yes** and a selected role, **Finish demo** shows a local-only completion confirmation; any **Existing demo** link opens `/demo` without carrying answers.
8. Changing **Yes** back to **No** blocks the wizard again without erasing answers already entered in the current page.
9. Wizard answers are not submitted, transmitted, or persisted, and no new case is created.
10. The new demo choices and flows are keyboard-accessible and usable on narrow screens; regression tests cover routing, non-upload behavior, wizard gating, and completion conditions.
