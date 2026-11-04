# Spec 21: Settlement Offer Response and Finalization

- **Status:** Implemented with limitation — secure local uploads and the authenticated response workflow are available; Google Drive Picker integration is unavailable.
- **Related issue:** [#74 — Track offer responses and guide accepted agreements to final forms](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/74)
- **Related specifications:** [Spec 16: Evidence-Traced Settlement Planning](../16-evidence-traced-settlement-planning/spec-16-evidence-traced-settlement-planning.md), [Spec 19: CR 2A Proposal and Property-Division Exports](../19-cr2a-property-division-exports/spec-19-cr2a-property-division-exports.md)
- **Objective:** Let an authorized case member record the exact proposal documents sent, track the other party's response, collect a counteroffer, and provide a carefully sourced final-document checklist after acceptance.
- **Scope:** Authenticated, authorized, non-demo case workflows. The public fictional demo must not accept real documents, access a user's Drive, or present the checklist as legal advice.
- **Legal-content boundary:** The application provides process prompts and links, not legal advice. Court forms, filing requirements, deadlines, and whether an agreed proposal resolves a judgment depend on the signed orders, case, and court. Users must review official court instructions and seek qualified Washington counsel or clerk guidance as appropriate.

## 1. Sent Documents and Response

- **FR-21-01 — Review and send prompt:** After document generation, tell the user to review and edit the drafts as needed, send the final documents to the other party themselves, and continue only after that step. The application does not send documents automatically.
- **FR-21-02 — Exact sent-file record:** In the authenticated case workspace, let the user attach the final DOCX and XLSX versions they actually sent. Accept local uploads and files selected from a connected Google Drive account. Display filenames, require explicit import, and use case-membership authorization and existing secure case-material storage. Do not copy real documents into the public demo.
- **FR-21-03 — Drive availability and permissions:** Offer Drive selection only when configured and connected. Use the narrowest supported Google authorization and read only user-selected files; do not make files public or expose access tokens to the browser or logs. If Drive selection is unavailable, explain why and preserve local upload.
- **FR-21-04 — Response outcome:** After recording the sent files, provide exactly three outcomes: counteroffer received, offer rejected, and offer accepted. Selecting an outcome is a user action and must not send documents, change legal case status, or invoke AI.
- **FR-21-05 — Counteroffer attachments:** Counteroffer requires at least one valid response attachment before Continue is enabled. Support local and configured Drive selection. The eventual destination after Continue is intentionally not defined; show a neutral placeholder rather than inventing a next legal step.
- **FR-21-06 — Rejection:** Rejection enables Continue to a neutral placeholder for a future workflow. Do not infer a legal consequence or create/send a document.
- **FR-21-07 — Acceptance:** Acceptance enables Continue to the final-document checklist, where the user can attach the document reflecting the offer the other party accepted. The accepted document remains user-provided; the application must not characterize it as court-filed, executed, or sufficient.
- **FR-21-08 — Accessible and responsive controls:** Announce upload, selection, outcome, validation, and error states accessibly. Keep the workflow keyboard-operable and usable on narrow screens in both themes.

## 2. Accepted-Offer Checklist and Official Sources

- **FR-21-09 — Findings and Conclusions:** Link “Findings and Conclusions About a Marriage” to the official Washington Courts **FL Divorce 231** PDF and the state divorce-forms index. Explain that users should confirm the correct form and current instructions for their case.
- **FR-21-10 — Judgment review:** Explain that the signed decree/order and docket control any money-judgment obligations and deadlines; do not state that every case has a judgment or that a certificate of dissolution resolves one.
- **FR-21-11 — Satisfaction of Judgment:** Do not present the King County District Court small-claims “Satisfaction of Judgment” form as a Superior Court family-law form. No current statewide Superior Court family-law form with that exact title has been verified for this workflow. Direct users to the Superior Court Clerk and official local family-law resources for the applicable filing document and procedure after a judgment is fully satisfied.
- **FR-21-12 — Final-payment stipulation:** Do not present “Stipulation and Order Regarding Final Payment of Judgment to Respondent” as a verified statewide form. If a judgment deadline may not be met, prompt users to seek advice promptly and explain that any agreed stipulation/order must be approved or accepted by the court as required; link to official local resources rather than fabricating or hosting an unofficial form.
- **FR-21-13 — Official references:** Provide the Washington Courts divorce-forms index, direct FL Divorce 231 download, King County Superior Court family-law resources, and RCW 4.64.080 for judgment-satisfaction context. Describe each link's scope accurately.
- **FR-21-14 — Counsel and clerk review:** Keep a visible note that forms, service, filing steps, and deadlines depend on the case and local court rules and that users should consult qualified Washington counsel or the clerk.

## 3. Privacy, Authorization, and AI Boundaries

- **FR-21-15 — Case authorization:** Protect every read, upload, selection, and state change with existing authenticated case-membership and permission checks. Do not trust a client-supplied case or file identifier without revalidation.
- **FR-21-16 — Privacy and retention:** Store attachments only within the authorized case-material system, enforce existing file type/size limits, and audit only minimal metadata. Do not log file contents, OAuth credentials, or document text.
- **FR-21-17 — No automatic AI processing:** Importing sent documents or counteroffers does not grant AI consent and does not trigger extraction or AI analysis. Any later analysis must use existing explicit consent controls.
- **FR-21-18 — Failure handling:** Surface unsupported files, missing Drive configuration, authorization failures, stale selections, and storage errors; do not report success when an import fails.

## 4. Acceptance Criteria

1. The authenticated user can record the exact sent DOCX and XLSX files using local upload or a configured, connected Google Drive selection.
2. The workflow offers the three specified response outcomes and does not infer a legal result.
3. Counteroffer Continue remains disabled until at least one response attachment is successfully imported; rejection Continue leads only to a neutral future-step placeholder; acceptance Continue leads to the checklist.
4. The checklist links FL Divorce 231 and verified official resources, and clearly marks the two judgment-related document names as unverified for statewide Superior Court family-law use.
5. Real documents never enter the public demo, become public Drive links, or reach AI automatically.
6. Existing case authorization, secure storage, file limits, audit boundaries, accessibility, and error handling remain in effect.

## 5. Verified Official References

- [Washington Courts Divorce (Dissolution) forms](https://www.courts.wa.gov/forms/?fa=forms.contribute&formID=13)
- [FL Divorce 231 — Findings and Conclusions About a Marriage (official PDF)](https://www.courts.wa.gov/forms/documents/FL%20Divorce%20231%20Findings-Conclusions-Marriage_2023%2007%2001.pdf)
- [King County Superior Court Family Law resources](https://kingcounty.gov/en/court/superior-court/courts-jails-legal-system/court-programs-children-families/divorce-custody-adoption/how-to-resources-family-law)
- [RCW 4.64.080 — Satisfaction of judgment](https://app.leg.wa.gov/RCW/default.aspx?cite=4.64.080)

## 6. Implementation Status

- The authenticated settlement-selection workspace now records and lists/reopens the final sent DOCX and XLSX, the user-selected response outcome, and any counteroffer attachment. Case membership and write permissions are checked; uploaded files use existing encrypted case object storage and validation limits. Imports do not trigger document extraction, AI, email, or third-party delivery.
- Local computer upload is supported. Google Drive Picker is not integrated: existing export OAuth does not provide a secure browser Picker flow or an endpoint for user-selected file bytes. The workflow explicitly reports this limitation and does not broaden Drive scopes or expose OAuth tokens.
- Acceptance displays the verified official links and the judgment/form caveats in section 5. Counteroffer and rejection continue only to a neutral placeholder.
