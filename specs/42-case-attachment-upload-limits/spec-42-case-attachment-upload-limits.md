# Spec 42: Case Attachment Upload Limits

- **Status:** Implemented
- **Related issue:** [#132 — Enforce per-file size and per-case attachment quotas](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/132)
- **Related issues:** #28 (materials import), #30 (secure storage), #84 (wizard attachments), #122 (Free/paid attempt-credit entitlement model)
- **Related specifications:** [Spec 05: Case-Materials Selection and Import](../05-case-materials-import/spec-05-case-materials-import.md), [Spec 06: Secure Case-Material Storage](../06-secure-case-material-storage/spec-06-secure-case-material-storage.md)
- **Superseded historical requirements:** The 20 MiB default per-file size in Spec 05 (FR-05-04 and its implementation note) is superseded by a 2 MiB (2,097,152 bytes) default. Spec 05 and Spec 06 are not edited; this spec is authoritative where they conflict.
- **Objective:** Bound case-attachment size and the number of stored attachments per case, enforced by the trusted server and mirrored in the UI for early feedback.

## Functional requirements

- **FR-42-01 — Per-file limit:** The default `MAX_UPLOAD_BYTES` is 2,097,152 (2 MiB). A file of exactly that size is accepted; one byte more is rejected server-side with HTTP 413 and a message naming the limit. The value stays configurable, and the UI displays the value the server reports rather than a hard-coded one.
- **FR-42-02 — Case-wide quota:** A case may hold at most 5 stored attachments on the Free plan and 100 on a paid plan. Every stored `documents` row of the case counts, whichever upload path created it.
- **FR-42-03 — Trusted entitlement:** The quota is derived only on the server. A case is paid when its attempt-credit ledger (Spec 29/#122) records a verified `package_purchase` entry; otherwise it is Free. A client-supplied tier or quota is never read. This spec sets no prices and defines no purchase flow.
- **FR-42-04 — Current count, not lifetime:** Only attachments currently stored count. A successful deletion releases the slot immediately; a failed deletion leaves the count unchanged.
- **FR-42-05 — Every upload entry point:** The size limit and quota apply to the secure materials import (device, and cloud providers once enabled), the case document extract/convert/render routes, and offer-response attachments. Routes whose providers or storage are disabled keep their existing fail-closed behavior (503) and are not enabled by this spec.
- **FR-42-06 — Over-quota rejection:** An upload that would exceed the quota is rejected with HTTP 409 and a message stating the current count, the limit, and that removing an attachment frees a slot. Nothing is stored for the rejected file.
- **FR-42-07 — Batches:** The materials UI uploads files individually. Files within the remaining slots are imported and kept; files beyond them are listed as rejected with the reason, never silently dropped or downgraded. Retrying a stored item (same batch and item id) returns the existing document and creates no duplicate and consumes no extra slot.
- **FR-42-08 — Concurrency:** The quota check and insert occur while the case row is locked in one transaction, so concurrent uploads cannot exceed the limit.
- **FR-42-09 — Usage display:** `GET /api/v1/materials/config` additionally reports `max_attachments` and `attachment_count` (for the optional authorized `case_id` query parameter; without it, 0 of the Free limit). The materials page shows "N of M attachments used" before and during selection.
- **FR-42-10 — Authorization:** Usage and uploads require the authenticated, authorized case membership already defined by Specs 03/06; non-members receive 404.

## Acceptance criteria

- Exactly 2 MiB is accepted; 2 MiB + 1 byte is rejected with 413.
- A Free case rejects its sixth attachment; a paid case rejects its 101st.
- Deleting an attachment lets a replacement be added immediately.
- Retries of a stored item do not duplicate or consume slots.
- Concurrent uploads never exceed the quota. Default tests (SQLite) verify only that the case row is locked (`FOR UPDATE`) before counting. Real parallel behavior is verified by the optional `PostgresConcurrentUploadTests`, which races two independent sessions for the last slot and requires exactly one success. It is skipped unless `WA_TEST_POSTGRES_URL` points to a disposable PostgreSQL database (e.g. `postgresql+psycopg://user:pass@localhost:5432/scratch`); it works in a throwaway schema it drops afterwards. Until it has been run in CI or deployment validation, parallel database behavior is not proven.
- Unauthorized users cannot read usage or upload.

## Out of scope

Pricing, plan purchase, per-user (rather than per-case) quotas, cloud-provider enablement, and changes to historical specs.
