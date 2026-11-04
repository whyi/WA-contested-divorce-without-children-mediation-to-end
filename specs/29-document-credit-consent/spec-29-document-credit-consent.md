# Spec 29: Explicit Proposal Document Credit Consent

- **Status:** In progress
- **Related issue:** [#90 — Charge document credits only after explicit proposal generation consent](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/90)
- **Related specification:** [Spec 28: Rejection Continuation and Negotiation Attempt Limits](../28-negotiation-attempt-limits/spec-28-negotiation-attempt-limits.md)
- **Objective:** Keep proposal review and editing free while clearly requiring and recording one document credit for each successfully generated proposal version.
- **Scope:** Authenticated real-case DOCX/XLSX downloads and direct delivery. Fictional demo exports and payment processing remain out of scope.

## Requirements

- **FR-29-01 — Free preview:** Viewing calculations and editing an unissued or unlocked proposal version do not consume document credits.
- **FR-29-02 — Explicit consent:** Generating a new version requires a server-checked confirmation flag. The UI states before generation that one credit covers both DOCX and XLSX files.
- **FR-29-03 — Pair pricing:** Successfully generating both formats for a proposal version consumes one credit total, regardless of which format was requested first. Direct delivery uses the same generation and credit path.
- **FR-29-04 — Immutable versions:** Persist each generated version's terms, scenario result, and both files. Re-downloading either format or delivering the same version does not consume another credit and uses the stored content.
- **FR-29-05 — Revised versions:** A user may explicitly unlock a new editable version of an un-frozen attempt. The prior version remains immutable. The new version costs one credit only when generation succeeds.
- **FR-29-06 — Atomic account ledger:** Serialize credit use against the account balance. Each successful new version records one debit with its resulting balance and a unique attempt/version idempotency key. Failed generation and repeated requests do not debit.
- **FR-29-07 — Insufficient balance:** Reject generation when the balance is insufficient, preserve the free editable preview, and return a clear error.
- **FR-29-08 — Trusted provisioning boundary:** Credits default to zero and are changed only by trusted server-side provisioning. Payment processing, price setting, and recurring allocation are out of scope.
- **FR-29-09 — Legacy versions:** Versions issued before this feature remain downloadable without a retroactive credit charge and are captured as immutable stored versions on their next download.

## Acceptance criteria

1. A direct API call cannot generate a new version without explicit credit consent and a sufficient server-side balance.
2. The first successful format generation stores both formats and consumes one credit; fetching the other format and retries are free.
3. Failed rendering or persistence leaves the balance unchanged.
4. Concurrent requests cannot debit the same version twice or overspend the account balance.
5. A changed proposal cannot overwrite a previously issued version; it requires explicitly unlocking and generating a separate version.
6. The UI identifies the credit cost and remaining balance before generation and explains that preview/editing is free.
7. Direct delivery cannot bypass credit consent or debit twice.
8. Legacy issued proposals remain available without retroactive billing.

## Implementation status

- Added zero-default account balances and an idempotent debit ledger.
- Persisted both generated file formats and the exact terms/scenario for each immutable version.
- Added server-enforced consent, balance checks, same-version free downloads, explicit new-version unlocks, and legacy backfill without retroactive charging.
- Updated the proposal UI to explain free preview/editing, the paired-file credit cost, and the remaining balance.
- Payment processing and automatic credit provisioning remain out of scope.
