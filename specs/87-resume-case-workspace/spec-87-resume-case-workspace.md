# Spec 87: Resume a progressed case instead of restarting onboarding

This additive specification amends spec 65's signed-in routing and spec 85's
starting-page routing. Existing specifications remain historical records.

- After successful document import and **Next**, persist `workspace_started`
  in case metadata before opening Asset Overview. This operation is idempotent,
  owner-only, authenticated, protected by the existing mutation controls, and
  serialized with other metadata writes using the case row lock.
- Home's **Your case**, other case entry links, direct signed-in entry, and login
  reopen a progressed case at `/case/assets?case_id=...`, not at the original
  upload screen or the mode-selection page. Use server state, not browser-only
  navigation history or a session storage flag.
- Dashboard summaries expose whether the workspace has started. For existing
  cases predating this fix, saved nondeleted documents, saved negotiation
  attempts, or saved asset snapshots also identify workspace progress.
- Preserve the explicit `?start_path=1` route used by document **Back**. Users
  can intentionally return to mode selection without clearing their progress
  or creating another case. New/unstarted cases retain existing onboarding.
- Once explicitly persisted, progress survives deletion of all uploaded files.
  It is not reset by visiting home, reloading, logging out, or reopening a case.
- A failed or unverified progress write keeps selection and uploaded files
  intact, reports the error, and permits retry without duplicate imports.
- Dashboard responses are not cacheable. Keep account ownership, lifecycle
  restrictions, preserved materials, and attempt finalization behavior unchanged.
- Verify upload → Next → logo → home → Your case → same Asset Overview, refresh,
  login, legacy progressed cases, explicit Back, and progress-write failure.
