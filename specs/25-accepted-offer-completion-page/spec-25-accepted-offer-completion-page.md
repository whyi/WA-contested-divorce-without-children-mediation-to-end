# Spec 25: Accepted Offer Completion Page

- **Status:** Implemented; automated tests passing
- **Related issue:** [#82 — Open a dedicated completion page after offer acceptance](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/82)
- **Related specifications:** [Spec 21: Settlement Offer Response and Finalization](../21-settlement-offer-response-and-finalization/spec-21-settlement-offer-response-and-finalization.md), [Spec 23: Explicit Sent Confirmation Freeze](../23-explicit-sent-confirmation-freeze/spec-23-explicit-sent-confirmation-freeze.md)
- **Objective:** Move accepted-offer completion guidance to a dedicated page reached by selecting Next after recording acceptance.
- **Scope:** Authenticated settlement workflows and the public fictional demo. The authenticated page must reload accepted-offer state through existing authorized APIs; the demo remains fictional and non-persistent.

## 1. Navigation and Content

- **FR-25-01 — Dedicated destination:** Accepted + Next navigates away from the response workflow to a distinct completion page. Do not reveal the completion checklist inline on the previous page.
- **FR-25-02 — Thank-you message:** Begin with a clear success/congratulations heading and a concise “Thanks for choosing Casework” acknowledgment.
- **FR-25-03 — Remaining document steps:** Explain that the user should complete Findings and Conclusions About a Marriage (FL Divorce 231) and attach the document reflecting the accepted offer.
- **FR-25-04 — Accurate court guidance:** Retain official Washington Courts links and existing caveats for judgment obligations, Satisfaction of Judgment, and any stipulation/order. Do not imply that a specific judgment or filing is universal or legally sufficient.
- **FR-25-05 — Accepted document attachment:** Keep the authorized secure accepted-offer upload available on the completion page. Restore its status from the existing response API after navigation.
- **FR-25-06 — Return path:** Provide a clear way back to the prior application workflow.

## 2. Context and Safety

- **FR-25-07 — Authenticated context:** Carry case and selection identifiers to the destination without embedding credentials or file contents. Load accepted state through the existing case-authorized endpoint; reject incomplete or non-accepted navigation with a visible status.
- **FR-25-08 — Demo behavior:** Accepted + Next in the demo opens its own completion route, displays fictional-only messaging, and does not upload, persist, or send files.
- **FR-25-09 — Other outcomes:** Counteroffer progression and rejection/placeholder behavior remain unchanged.
- **FR-25-10 — Accessible page:** Use a page-level heading, visible loading/error status, descriptive upload label, and responsive theme-consistent layout.

## 3. Acceptance Criteria

1. Accepted + Next navigates to a separate URL/page; no completion guidance appears inline on the response screen.
2. The new page shows congratulations and thanks, FL Divorce 231 guidance, accepted-offer attachment, official links, and existing legal caveats.
3. Authenticated navigation restores the accepted attempt and attachment state through authorized APIs.
4. Demo navigation is separate, fictional, and non-persistent.
5. Counteroffer and rejection behavior is unchanged.

## 4. Implementation Status

- Accepted + Next in both the authenticated workflow and public demo navigates to a dedicated completion URL. The response page no longer contains or reveals the completion checklist.
- The authenticated destination reloads the attempt through the existing authorized API and shows the secure accepted-document attachment only for an accepted, sent-confirmed attempt.
- The public demo destination is explicitly fictional and does not upload, persist, or send documents.
- Official Washington Courts links and existing judgment/process caveats are retained on the completion page.
- Focused and complete automated test suites pass.
