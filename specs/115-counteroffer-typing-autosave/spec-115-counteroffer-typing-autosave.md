# Spec 115: Focus-Preserving Counteroffer Autosave

- **Tracking issue:** [#368](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/368)
- **Amends:** Specs 113 (counteroffer Next readiness) and 114 (reopened
  counteroffer details), only for the notes autosave interaction. Historical
  specifications remain unchanged.

## Requirements

1. Typing in **Notes about the counteroffer** must not require blur, refocus,
   or another click to update Next readiness. After the existing debounce and
   successful persistence of the latest input, enable Next automatically.
2. Background notes autosave must not disable the editable textarea, steal
   focus, reset the caret, or overwrite newer text. Keep other mutation
   controls and Next disabled while the request is in flight.
3. If notes change during a save, preserve the current draft and serialize
   another save using the returned revision. Do not mark the draft saved or
   enable Next until the latest text is persisted.
4. On failure keep the current draft, focus, and explicit error; Next remains
   disabled. Further input retries saving without requiring focus changes.
   Never automatically loop on an unchanged failed request.
5. Apply to ordinary and latest reopened editable counteroffers, desktop and
   mobile. Preserve native disabled state for empty/whitespace-only notes with
   no attachment, saved-file readiness, quota/subscription dialogs, explicit
   mutations, upload locking, and historical/closed read-only behavior.

## Regression coverage

Use actual keyboard events, retain textarea focus through delayed saves, type
additional text while a save is pending, and verify revision-ordered persistence,
automatic Next enablement, failed-save retry, popup behavior, and reload.
