# Spec 27: Review Modified Offers Before Sending

- **Status:** In progress
- **Related issue:** [#86 — Add unchanged-versus-modified offer confirmation before freezing an attempt](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/86)
- **Related specifications:** [Spec 21: Settlement Offer Response and Finalization](../21-settlement-offer-response-and-finalization/spec-21-settlement-offer-response-and-finalization.md), [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 23: Explicit Sent Confirmation Freeze](../23-explicit-sent-confirmation-freeze/spec-23-explicit-sent-confirmation-freeze.md)
- **Objective:** Distinguish sending an unchanged proposal from sending a modified offer, require modified DOCX/XLSX uploads, review supported parsed changes, and use the reviewed fields to start the next attempt.
- **Scope:** Authenticated offer-response flow and its authorized secure attachments. The fictional demo remains unchanged.

## 1. Sending Choice

- **FR-27-01 — Explicit unchanged choice:** Replace the single confirmation with **I reviewed and sent the final documents**, described as the same proposal the user downloaded or the terms/values currently shown. It preserves the existing DOCX/XLSX upload, sent confirmation, freeze, and response flow.
- **FR-27-02 — Explicit modified choice:** Offer **I modified the offer**. Selecting it reveals two required inputs with the label **Upload the modified offer here**: one DOCX and one XLSX.
- **FR-27-03 — Fail-closed upload gate:** The modified path cannot be confirmed or continued until both supported files are successfully uploaded, parsed, and the parsed fields are reviewed and explicitly accepted. Upload or parsing failures must be visible and retryable.

## 2. Parse, Review, and Inherit

- **FR-27-04 — Supported-field parsing:** Parse only recognized offer fields from DOCX and XLSX, including party/caption fields, dates, terms, and recognized proposed allocations. Preserve the existing case snapshot as the source for known asset IDs. Never execute workbook formulas or treat formula results as verified facts.
- **FR-27-05 — Explicit review:** Show parsed values and any unrecognized or ambiguous rows for user review. Do not silently claim unparsed edits were imported. A user must explicitly accept the parsed draft before sent confirmation is enabled.
- **FR-27-06 — Next-attempt prefill:** When a counteroffer creates the next attempt, use the reviewed parsed fields as its editable state; do not modify the frozen prior attempt.
- **FR-27-07 — Source attachments:** Keep both modified documents securely attached to the attempt and visible/downloadable as source files on the next attempt. Enforce existing case authorization and storage controls.

## 3. Safety and Compatibility

- **FR-27-08 — Validation and security:** Validate DOCX/XLSX containers, size, extension, and contents using existing upload validation. Parse server-side without macros or formula evaluation. Do not expose attachments across cases.
- **FR-27-09 — Unchanged behavior:** Selecting the unchanged path retains current confirmation/freeze behavior. Counteroffer, rejection, and accepted-offer behavior remain unchanged.
- **FR-27-10 — Accessible status:** Make choice, upload progress/errors, parsed review, and confirmation state keyboard-operable and announced using existing status patterns.

## 4. Acceptance Criteria

1. The sent-document checkpoint presents the unchanged and modified choices with clear supporting text.
2. The modified path requires both DOCX and XLSX files and explicit review/acceptance of parsed fields before freezing.
3. Supported parsed fields populate the editable next attempt after counteroffer; the previous frozen attempt remains unchanged.
4. Both modified files remain available as authorized references on the next attempt.
5. Invalid, malformed, oversized, mismatched, or ambiguous files fail visibly and cannot be treated as successfully sent.
6. The unchanged path preserves existing behavior.
7. Tests cover parsing, API authorization/storage, upload and review gates, next-attempt inheritance, and unchanged-path compatibility.

## 5. Implementation Status

- Implemented in authenticated offer-response workflows. Modified DOCX and XLSX
  files are stored separately from unchanged-path attachments and are parsed
  server-side without evaluating workbook formulas.
- Parsed fields remain editable until the user explicitly accepts the review.
  Replacing a modified file invalidates a prior acceptance; the server also
  verifies the files and review state before freezing the attempt.
- Reviewed values seed the next counteroffer attempt, and both source files are
  preserved there as authorized downloadable attachments.
- Validation completed with the repository harness and focused parser,
  authorization, confirmation, and inheritance tests.
