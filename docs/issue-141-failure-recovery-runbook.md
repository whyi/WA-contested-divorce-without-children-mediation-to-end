# Failure recovery runbook

This runbook covers upload, extraction/OCR, consented AI analysis, proposal generation, and download failures. It does not replace the preservation/credit remedy in [Spec 38](../specs/38-failure-recovery/spec-38-failure-recovery.md).

## User recovery

- **Upload:** The app reconciles the import batch/item before retrying. If absent, ask the user to reselect the same file; never reuse an item identity for different bytes. Successful sibling uploads remain stored.
- **Extraction/OCR:** Retry only a `failed` job against its unchanged source. For `needs_attention`, check the safe error code; OCR-dependent, unsupported, and unreadable files need an appropriate source/OCR path rather than repeated retry. The original source remains stored.
- **AI analysis:** Retry only the failed document job with its original active consent and source. Do not repeat successful sibling jobs. If consent is revoked or unavailable, obtain fresh explicit consent through the normal flow.
- **Proposal generation:** Reload the saved attempt before retrying. Failed finalization preserves editable work and does not permanently debit a credit. The finalized snapshot is immutable.
- **Download/uncertain result:** First reload attempt status. If it is finalized, redownload the same snapshot (free and idempotent). If it remains editable, retry finalization. A download click does not establish that the file reached a recipient.

## Severity, routing, and response

- **SEV1 — systemic or integrity risk:** Failures affect multiple users/workflows, persisted work may be lost/corrupted, or credit/finalization state is inconsistent. Route to the deployment's urgent incident channel and investigate immediately under the operator-approved response target.
- **SEV2 — isolated processing failure:** A single operation failed while saved work and accounting remain intact. Route to the configured application-support queue; reconcile the state and help the user use the safe retry path.
- Stable application event codes include `upload_storage_failed`, `upload_persistence_failed`, `extraction_job_failed`, `analysis_job_failed`, `proposal_generation_failed`, and `document_download_failed`. The current app emits safe server-side log events; alert delivery/grouping is owned by the deployment's existing log/alert system.
- A browser-only interrupted download cannot be detected by the server after a successful response. The UI offers a user-initiated safe diagnostic summary; the event reaches support only if the user chooses to share it. This remains a deployment/product acceptance gap until a support destination and alert intake are configured.
- Group repeated events by event code and configured time window/threshold. Do not set an arbitrary retry ceiling or assume that a single failed job is systemic.
- Set actual alert routes, on-call ownership, and response targets before production use. This repository does not configure a monitoring vendor or establish an SLA.

## Required deployment values

Complete and verify these values in the deployment's protected configuration before launch:

```text
SUPPORT_CONTACT_URL=<HTTPS support destination approved by the operator>
FAILURE_ALERT_SEV1_ROUTE=<existing urgent incident route>
FAILURE_ALERT_SEV2_ROUTE=<existing application-support route>
FAILURE_ALERT_GROUPING_WINDOW=<operator-selected window>
FAILURE_ALERT_GROUPING_THRESHOLD=<operator-selected threshold>
FAILURE_ALERT_SEV1_RESPONSE_TARGET=<operator-approved target; not an SLA supplied by this repo>
FAILURE_ALERT_SEV2_RESPONSE_TARGET=<operator-approved target; not an SLA supplied by this repo>
ON_CALL_OWNER=<operator-defined role/team>
```

`SUPPORT_CONTACT_URL` is optional in local development; when absent, the UI offers copyable diagnostics but no fabricated contact. Configure a public HTTPS destination without embedded credentials or query parameters. Alert placeholders must be mapped by the deployment's existing log/alert system; setting these strings without routing rules does not create alerts.

## Privacy and triage

The copyable user diagnostic includes only operation category, UTC timestamp, HTTP status when available, a known safe error code, and a random client reference. It is not automatically sent. Ask the user to share it only through the configured support destination. Search operator logs by event code and time. Never ask for or log case materials, filenames, account/case/document IDs, object keys, access tokens, cookies, credentials, prompts, extracted text, or raw provider output.

The repository's Docker image disables Uvicorn access logs because request paths contain case and document identifiers. Any alternate server or reverse proxy must similarly disable access logging or redact resource identifiers before storing or forwarding logs.

Confirm persistence and status through authenticated application workflows. Do not manually re-run jobs or alter the credit ledger outside the existing idempotent retry/finalization paths. Escalate inconsistent finalization, duplicate artifacts, or missing persisted user work as SEV1.
