# Spec 79: Real case workspace navigation

## Amendment

This additive specification amends Spec 76's exclusion of real-account attempt navigation. It restores only the demo's case-navigation structure, saved attempt-profile viewing, Asset Overview, and case file management for authenticated cases. It does not restore the deleted technical planner, scenario JSON, AI consent, proposal generation, final-download flow, or next-attempt creation.

## Requirements

- Real document, wizard, asset, and file screens display the shared case header, ordinal attempt navigation, Asset Overview, and Case file management links.
- Navigation remains scoped to the authenticated case ID and never directs a real case into fictional demo routes.
- A case with no negotiation attempt displays its first preparation stage, explicitly identifying that no attempt is saved. Saved ordinals come from server records; the next future marker is disabled and does not create an attempt or imply purchased credit.
- Asset Overview displays saved property records, wizard asset/debt entries, recorded relationship dates, and additional inventory values without fictional defaults, invented ownership, legal classifications, duplicated aggregation, or unavailable amounts rendered as zero.
- Previously saved attempt profiles are read-only and use the finalized/frozen snapshot when available. Current wizard values must not be substituted for historical values absent from snapshots.
- Case file management lists actual server documents and supports authenticated downloads, explicit permanent deletion, refresh, and the existing upload workflow. Original filenames are unavailable in the current storage model; identify files by document ID.
- The workspace API applies existing case authorization and deletion barriers, excludes tombstoned documents, responds with `Cache-Control: no-store`, and logs retryable database errors.
- Invalid/missing case IDs, unavailable attempts, and read failures show explicit errors rather than sample figures or empty success-shaped fallbacks.
- Preserve direct documents/wizard entry, conditional offer visibility, the single document Back button, and fictional demos.

## Verification

Browser regressions cover real case navigation, actual saved values, absent values, historical snapshot isolation, reload, file links, and unavailable attempts. Backend tests cover snapshot precedence, persisted intake/documents, tombstone filtering, case rejection, and logged database failures. Validate the running local HTTPS server with a fictional authenticated account without altering production.
