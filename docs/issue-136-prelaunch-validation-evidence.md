# Issue 136 pre-launch validation evidence

**Status:** Partial engineering evidence only; not launch approval or a conformance claim.
**Base:** `origin/main` at `fdacc92cdf68e11c40f217090b26978833b8f7c4` (PR #164 merged).
**Scope:** Specs 05, 32, 35, 39, 40, 42, 45, and 46; issue #136.

## Automated and local checks performed

- Focused Python suite: 102 tests passed; 1 optional PostgreSQL concurrency test skipped because no `WA_TEST_POSTGRES_URL` was configured.
- Full Python suite: 493 tests run; 1 skipped and 1 failed. The failure is `test_main.MainWorkflowTests.test_theme_selection_persistence_and_shared_page_coverage`: its no-hex-color regex rejects the existing `#17241f` preview-bar color. The color is unrelated to these changes and is also documented as a known failure in the current comparison/rejection specifications.
- Local application: `/healthz` returned `{"status":"ok"}`. `/`, `/demo`, `/demo/documents`, `/demo/wizard`, `/demo/rejection-completion`, and `/rejection-completion` each returned HTTP 200 with case APIs and demo mode disabled. This confirms route availability only; it is not an interactive or authenticated workflow test.
- Source/test inspection found existing focus-visible styles, live status/error semantics, comparison alternatives, and the labeled comparison-table pattern. These are source observations, not proof of rendered layout or screen-reader behavior.
- No accessibility scanner was present in the declared dependency tree/tooling, so none was installed or run.
- A follow-up static DOM audit of the fictional demo page found 193 interactive controls, no unnamed controls, no duplicate IDs, no unresolved `aria-labelledby`/`aria-describedby` references, no fieldsets without legends, and no images missing `alt`. This does not measure rendered layout or actual assistive-technology behavior.
- The integrated browser remained unable to connect to the preview at `http://127.0.0.1:8890/demo` and `http://192.168.1.17:8890/demo`; the same preview returned HTTP 200 to local `curl`.
- Regression tests in `tests/test_accessibility_markup.py`: 4 passed for accessible names, ARIA references, unique IDs, fieldset legends, and image alt attributes. Related UI test run: 39 tests, with the same known theme-color regex failure (`#17241f`); no other failure.

## Browser and manual checks not completed

The integrated browser could not reach the local preview at `http://localhost:8000/demo/documents` (navigation timed out); attempting navigation from an available browser page also timed out. Direct `file:` access to the checkout was blocked by the browser's trusted-folder restriction. Consequently:

- No actual browser tests were completed at 320, 375, 768, or 1280 CSS pixels, and no screenshots or rendered-DOM measurements are available.
- No keyboard/focus interaction was performed for upload select/remove, editing comparisons, finalization confirmation/cancellation, or errors/recovery.
- No screen reader or other assistive technology was run. No AT/browser combinations are asserted.
- No authenticated case flow, upload, backend persistence, or provider integration was exercised; the local routes were static-preview responses with authentication and demo mode disabled.

These are not passes. Browser-matrix approval, accessibility target approval, AT combinations, and release-blocking policy remain product decisions. WCAG 2.2 AA is recorded in Spec 47 only as a proposed baseline pending approval, not as an achieved or official conformance claim. Issue #136 remains open.

## Reproducibility

Run the focused suite from the repository root with:

```sh
python3 -m unittest tests.test_materials tests.test_upload_validation tests.test_offer_comparison tests.test_attempt_finalization tests.test_rejection_completion tests.test_failure_recovery tests.test_case_lifecycle tests.test_attachment_limits
```

Run the full suite with:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

The application preview was run with an isolated SQLite URL and auth/demo disabled; the application health and listed GET routes were probed locally. It did not use real case data or external services.
