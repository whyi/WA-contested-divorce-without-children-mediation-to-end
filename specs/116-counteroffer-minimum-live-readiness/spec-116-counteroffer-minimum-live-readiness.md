# Spec 116: Counteroffer Minimum and Live Next Readiness

- **Tracking issue:** [#370](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/370)
- **Amends:** Specs 113, 114, and 115 only for counteroffer notes readiness.
  Prior specifications remain unchanged.
- **Approved minimum:** 150 Unicode code points after trimming leading/trailing
  whitespace. Internal spaces count. A saved counteroffer attachment is an
  alternative; selecting a file whose upload failed is not sufficient.

## Requirements

1. For ordinary and latest reopened real counteroffers, update Next from the
   current textarea value on every input event, not blur, refocus, a debounce,
   or the previous saved value. Show the 150-character-or-file rule.
2. With no saved file, 0 through 149 trimmed characters remain disabled before
   and after save, blur/refocus, and reload. At 150 or more, enable immediately
   while focused, unless a mutation is in progress or persistence failed.
   Deleting below the minimum disables immediately.
3. This intentionally supersedes the earlier requirement to wait for autosave
   before enabling a valid draft. Clicking Next cancels pending debounce,
   persists the latest notes, and only then shows the existing quota/subscription
   dialog or continues. Failed persistence never advances or shows success.
4. Preserve textarea focus and caret during background saves, serialize newer
   drafts, and do not overwrite unsaved input. A failed save keeps the draft,
   announces the error and disables Next. A new valid edit permits retry;
   progression still requires a successful save.
5. Backend continuation rejects short notes without a saved attachment; saving
   incomplete drafts remains allowed. Preserve attachment validation/quotas,
   server quota enforcement, historical/closed locks, ownership and CSRF.
6. Deploy the PR revision to the HTTPS 8002 preview after PR creation. Verify
   the served revision, authenticated login, and live threshold/focus behavior.
   Do not reset accounts or overwrite actual case materials for UI probes.

## Regression coverage

- Assert 1, 149, 150 and 151 characters, trimmed whitespace, Unicode, immediate
  input enablement, deletion, blur/refocus, save failure, reload, and saved-file
  override on desktop/mobile and ordinary/reopened attempts.
- Use keyboard input and verify active element/caret without outside clicks.
- Hold a save request to prove Next persists before showing a popup.
- Exercise the live served HTML with read-only real API calls and isolated
  response-write fixtures so no user case changes are persisted.
