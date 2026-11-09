# Approved Page Inventory Audit

This is a historical source-and-route audit, not a product specification or authorization to remove or merge screens. It records the inventory reviewed for [issue #262](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/262) against source commit `4101519274d06d515c1e33ff141d71aa5036c888`. Later changes may make individual findings stale; re-audit the current source before implementation.

## Owner-approved page types

1. Landing
2. Mode/start choice
3. Wizard
4. Attempt
5. Offer accepted
6. Account

## Additional screens identified

| ID | Screen | Entry point | Decision needed |
|---|---|---|---|
| X-01 | Real-account materials/upload preparation | `/onboarding/upload?case_id=...` | Decide whether to embed document preparation in an approved page type. |
| X-02 | Demo documents selection | `/demo/documents?source=...` | Decide where the separate file-selection flow belongs. |
| X-03 | Demo case file management | `/demo/files?source=...` | Decide whether to merge it into Attempt or Account. |
| X-04 | Real offer-rejected / mediation-stopped completion | `/rejection-completion?case_id=...` | Preserve close/reopen behavior if this screen is merged or removed. |
| X-05 | Demo offer-rejected / stopped completion | `/demo/rejection-completion?source=...` | Decide whether a separate demo completion screen is permitted. |
| X-06 | Google Drive connection result popup | Google Drive callback route | Decide whether provider result popups are explicit exceptions. |
| X-07 | Dropbox connection result popup | Dropbox callback route | Decide whether provider result popups are explicit exceptions. |
| X-08 | Swagger API documentation | `/docs` | Decide whether owner UAT should expose or disable framework docs. |
| X-09 | ReDoc API documentation | `/redoc` | Decide whether owner UAT should expose or disable framework docs. |
| X-10 | Swagger OAuth redirect helper | `/docs/oauth2-redirect` | Decide whether this technical helper should remain reachable. |

## Other findings requiring explicit decisions

- Real and demo Attempt screens had materially different interfaces. Calling both Attempt does not establish that they meet the intended shared-page design.
- A closed-only account was routed to Account rather than mode choice or Attempt.
- Login, signup, and verification were forms within Landing; nested preparation and Attempt panels were not standalone routes.
- Error states, API responses, downloads, external provider pages, and redirect aliases were distinguished from product pages.
- The prior audit did not authorize changing disclosures, deleting functionality, or consolidating screens.

## Follow-up

Resolve the decisions tracked in issue #262 before creating a page-inventory specification or changing navigation. Any approved change should preserve upload and processing, consent, closure/reopen, disclosure, and provider error reporting behavior.
