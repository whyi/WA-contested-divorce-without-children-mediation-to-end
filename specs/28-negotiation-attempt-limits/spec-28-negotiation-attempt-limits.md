# Spec 28: Rejection Continuation and Negotiation Attempt Limits

- **Status:** In progress
- **Related issue:** [#88 — Limit negotiation attempts and continue after rejection](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/88)
- **Related specifications:** [Spec 22: Versioned Settlement Negotiation Attempts](../22-versioned-settlement-negotiation-attempts/spec-22-versioned-settlement-negotiation-attempts.md), [Spec 23: Explicit Sent Confirmation Freeze](../23-explicit-sent-confirmation-freeze/spec-23-explicit-sent-confirmation-freeze.md), [Spec 27: Review Modified Offers](../27-modified-offer-review/spec-27-modified-offer-review.md)
- **Objective:** Allow rejected offers to continue without an attachment, show and enforce account attempt limits, and close the repeated-export/edit loophole.
- **Scope:** Authenticated real-case settlement negotiation and DOCX/XLSX exports. Fictional demo and payment processing remain unchanged.

## 1. Rejected Offer Continuation

- **FR-28-01 — Rejection continuation:** Selecting **Offer rejected** shows the same saved continuation path as **Counteroffer received**, with the message “Continue to revise offer or stay here. Everything is saved. Come back if things change.”
- **FR-28-02 — No rejection attachment:** Rejected offers may continue immediately without uploading a response document. Counteroffers still require their received document. Not pressing Continue leaves the saved attempt available.
- **FR-28-03 — New attempt:** Continue from either a rejection or an attached counteroffer creates/reopens the next numbered editable attempt, subject to entitlement. The frozen predecessor remains unchanged.

## 2. Trusted Attempt Entitlement

- **FR-28-04 — Server-side plan limit:** Store a trusted account entitlement on the user record. The default Free limit is 1 total attempt per case; paid entitlement values are 3, 5, and 10 total attempts. The API never accepts a client-supplied plan, limit, or ordinal.
- **FR-28-05 — Safe payment boundary:** No billing provider exists in the repository. Payment processing is out of scope; only trusted server-side provisioning may change the entitlement. Unknown or absent entitlement uses the Free limit.
- **FR-28-06 — Exhaustion:** Block creating or issuing an attempt beyond the limit, return a clear conflict response, preserve existing case history, and allow reading prior attempts. `attempts_remaining` is the maximum total minus the current ordinal, clamped to zero.
- **FR-28-07 — Atomic transition:** Serialize case transitions and enforce the limit in the server transaction so parallel/replayed requests cannot create extra attempts.

## 3. Proposal-Issuance Lock

- **FR-28-08 — Lock first issued draft:** The first successful real-case DOCX or XLSX export stores the validated offer terms and issuance timestamp on the active attempt. It locks that attempt's terms, values, and scenario inputs against further updates.
- **FR-28-09 — Same immutable pair:** The other document format and later downloads can only use the pinned terms and scenario. Requests with altered terms fail visibly; repeat downloads of the same version are idempotent and do not consume additional attempts.
- **FR-28-10 — Server-side guards:** Enforce the issuance lock on all attempt-state and document-export endpoints, not only disabled browser controls. Only an authorized, quota-checked rejection/counteroffer transition can create the next editable attempt.
- **FR-28-11 — Modified documents:** Preserve the Spec 27 requirement to upload modified DOCX/XLSX and explicitly review them before confirmation. They remain attached to their issued attempt and cannot be used to unlock or revise that attempt in the app.

## 4. Accessible Limit Display

- **FR-28-12 — Attempt counter:** Show `Attempt N of M` in the active attempt UI and response history. When exhausted, explain that the current tier has no attempts remaining and keep the prior attempt readable.
- **FR-28-13 — Rejection action state:** Rejected and counteroffer outcomes both explain that the user's saved data remains available. Disable the continue action only when the attempt limit is exhausted; counteroffer also remains disabled until its attachment is present.

## 5. Acceptance Criteria

1. Rejection continues without an attachment; a counteroffer still requires one.
2. Both transitions use the same next-attempt flow and keep the old attempt frozen.
3. Free/3/5/10 limits come from a trusted server-side account entitlement and are enforced by direct API calls as well as the UI.
4. The first generated format pins terms and blocks edits; the other format and retries use the same pinned content.
5. Replaying a download does not consume quota or create a different proposal; changing its request is rejected.
6. Attempt display and remaining count remain correct after reload and across case history.
7. Tests cover each limit, exhausted rejection and counteroffer, missing/present counteroffer attachments, replay/concurrent transitions, direct state updates after issuance, and paired DOCX/XLSX output consistency.

## 6. Implementation Status

- Implemented server-managed `settlement_attempt_limit` values of 1, 3, 5, and 10; new accounts default to Free (1). Payment processing and entitlement administration remain out of scope.
- Rejection now follows the same next-attempt transition as a counteroffer, without requiring an attachment. Counteroffers still require their file.
- DOCX, XLSX, and delivery routes pin the first successfully rendered proposal terms and scenario on the attempt. Later exports must match those terms and use the pinned scenario.
- Attempt-state updates reject changes to the issued offer and scenario. Workflow-only state changes for the modified-offer review remain available.
- The response and history views report `Attempt N of M` and remaining attempts.
- Focused tests cover entitlement values/defaulting, exhausted rejection/counteroffer transitions, immutable cross-format exports, stale case revisions after issuance, and direct attempt-state edits.
