# Spec 101: Counteroffer footer at the attempt limit

This additive specification amends the counteroffer plan-limit placement in
[spec 94](../94-counteroffer-next-upgrade/spec-94-counteroffer-next-upgrade.md).
Existing specifications remain unchanged.

## Requirements

- In real-case counteroffer views, replace the bottom notes/attachments helper
  with `Your paid plan allows 3 attempts. The attempt limit is reached.` when
  the current attempt ordinal has reached the server-provided attempt limit.
- Derive the plan label, number, and singular/plural wording from the existing
  server state. Free therefore reads `Your Free plan allows 1 attempt. The
  attempt limit is reached.` Other paid limits use their actual value.
- Show this limit explanation once, at the footer, not again above the response
  controls. Preserve error/status messages and the existing credit notice.
- When quota remains, retain `Notes and attachments are saved to your case.
  They are not automatically sent or analyzed.` Inactivity alone is not quota
  exhaustion.
- Preserve saved notes/files, autosave, reload behavior, read-only protections,
  server limit enforcement, and fictional-demo behavior.

## Regression coverage

Chromium entry tests cover Free exhaustion, paid 3/3 exhaustion, paid 2/3 with
quota remaining, and a closed case with quota remaining. Verify exact footer
copy after reload, hidden duplicate messaging, and preserved saved notes.
