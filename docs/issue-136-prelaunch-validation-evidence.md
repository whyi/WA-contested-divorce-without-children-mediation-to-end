# Issue 136 pre-launch validation evidence

**Status:** Partial engineering evidence only; not launch approval or a conformance claim.
**Base:** `origin/main` at `5197c677d9053eb181253d746018f5e119cf11dc` (PR #168 merged).
**Scope:** Specs 05, 32, 35, 39, 40, 42, 45, and 46; issue #136.

## Automated and local checks performed

- Refreshed focused Python suite on the current base: 107 tests passed; 1 optional PostgreSQL concurrency test skipped because no `WA_TEST_POSTGRES_URL` was configured.
- Refreshed full Python suite: 548 tests run; 2 skipped and 1 failed. The failure is `test_main.MainWorkflowTests.test_theme_selection_persistence_and_shared_page_coverage`: its no-hex-color regex rejects the existing `#17241f` preview-bar color. The color is unrelated to this validation and is documented as a known test issue.
- Local application: `/healthz` returned `{"status":"ok"}`. `/`, `/demo`, `/demo/documents`, `/demo/wizard`, `/demo/rejection-completion`, and `/rejection-completion` each returned HTTP 200 with case APIs and demo mode disabled. This confirms route availability only; the separate demo-only browser interactions below do not verify authenticated or persisted workflows.
- Source/test inspection found existing focus-visible styles, live status/error semantics, comparison alternatives, and the labeled comparison-table pattern. These are source observations, not proof of rendered layout or screen-reader behavior.
- No accessibility scanner was present in the declared dependency tree/tooling, so none was installed or run.
- A follow-up static DOM audit of the fictional demo page found 193 interactive controls, no unnamed controls, no duplicate IDs, no unresolved `aria-labelledby`/`aria-describedby` references, no fieldsets without legends, and no images missing `alt`. This does not measure rendered layout or actual assistive-technology behavior.
- The integrated browser remained unable to connect to the preview at `http://127.0.0.1:8890/demo` and `http://192.168.1.17:8890/demo`; the same preview returned HTTP 200 to local `curl`.
- Regression tests in `tests/test_accessibility_markup.py`: 4 passed for accessible names, ARIA references, unique IDs, fieldset legends, and image alt attributes.

## Additional local rendered-browser checks

The integrated browser service was unavailable during this follow-up, so a temporary local headless Playwright 1.64.1 installation and Chromium 156.0.8078.4 were used against an isolated preview at `http://127.0.0.1:8890`. The app ran with authentication, case-data access, and demo mode disabled, using a temporary SQLite database; the inspected `/demo` routes explicitly identify themselves as fictional previews and do not open active case workspaces.

- `/demo`, `/demo/documents`, `/demo/wizard?source=demo2`, `/demo/2/dashboard`, and `/demo/settlement-completion` each returned HTTP 200 at 320, 375, 768, and 1280 CSS pixels. On all 20 route/viewport combinations, `document.documentElement.scrollWidth` and `document.body.scrollWidth` equaled the viewport width (320, 375, 768, and 1280 respectively); no page-level horizontal overflow was measured.
- The main content widths on `/demo/documents` were 280, 335, 700, and 1172 CSS pixels at the four viewport widths. At 320 pixels, the comparison editor's asset table remained a 630-pixel scrollable region inside a 202-pixel client area, while the document remained 320 pixels wide. This is the intended table-level horizontal scroll, not page-level overflow.
- At 320 pixels, the first 20 Tab stops on the documents preview, wizard preview, and demo dashboard were visible and had a computed solid 3-pixel outline. This was an automated keyboard-focus smoke check, not a complete manual focus-order audit.
- A synthetic in-memory `sample.pdf` selection on `/demo/documents` displayed the selected filename; activating Remove removed the selection and displayed “sample.pdf removed. Selected files remain on this page only.” The preview stated that files are not uploaded or saved. This verifies only the fictional browser-local preview behavior, not backend upload persistence or failure recovery.
- The demo's asset editor exposed labeled amount fields at 320 pixels, and its horizontal scrolling was contained as described above. Activating its “I reviewed and sent the final documents” preview control displayed the frozen-attempt message. This does not verify the authenticated finalization confirmation/cancel flow, persisted snapshots, downloads, or credit handling.

The temporary Playwright package and browser were installed outside the repository; no project dependency or production configuration was changed. The evidence is limited to one Chromium build, headless emulation, and fictional demo pages. No approved browser/device support matrix, real-device run, screen reader/assistive technology combination, full keyboard workflow, authenticated case flow, or formal accessibility conformance evaluation was performed.

## Browser and manual checks not completed

The integrated browser could not attach to the local preview at `http://127.0.0.1:8890/demo` or `http://192.168.1.17:8890/demo`; direct local Chromium checks above were used instead. The same preview returned HTTP 200 to local `curl`. Consequently:

- No browser/device support claim is made from the single headless Chromium run; physical mobile devices and additional browsers remain untested.
- No complete keyboard pass was performed for upload select/remove, comparison editing, finalization confirmation/cancellation, and error/recovery. The focus smoke check above does not cover every workflow state.
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
