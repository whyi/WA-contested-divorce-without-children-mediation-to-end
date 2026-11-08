# Spec 71: Executable Signed-In Entry Contract

- **Related issue:** [#258](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/258)
- **Amends:** Spec 65 FR-65-01 and Spec 66 FR-66-04. Every active case opens its attempt workspace from successful sign-in and authenticated root entry, including incomplete wizard and documents cases. Preparation completion is no longer an entry gate. Spec 70's attempt-first presentation is retained.
- **Supersedes:** The automatic preparation redirects and wizard-completion check in those prior entry requirements. Historical specs remain unchanged.

## Requirements

1. Successful sign-in and authenticated `/` visits with no owned case open the new-case documents/wizard start choice directly.
2. With an active case, those entry points show that case's attempt workspace immediately, regardless of preparation mode or draft completeness. Do not fetch wizard intake to decide entry, or redirect to preparation, a case list, Account, or the home landing screen.
3. **Edit case information** still explicitly opens the case's saved wizard/documents path. Explicit Account and Home navigation, signed-out handling, closed-case reopen/export behavior and failed status requests are unchanged.
4. The entry attempt view contains attempt progress and scenario work, not a visible legacy introduction, expanded ledger editor or case-list heading. Preserve calculation, persistence, disclosure availability and document gates.
5. Run real Chromium regression tests on `main` push and pull requests. Load the complete repository HTML and execute its actual startup, sign-in form handler, fetch calls, DOM rendering and reload behavior. Use synthetic API fixtures, never a deployed account or real credentials.
6. Cover no case, active cases with no preparation path, documents path, and both incomplete/complete wizard drafts; successful login and authenticated refresh. Assert actual destination, visibility of the attempt or start choice, hidden forbidden screens, and absence of intake-gated redirects. Cover expired login sessions and failed dashboard requests without a success-shaped fallback.
7. Unexpected same-origin requests and browser script errors fail the test. Third-party traffic is blocked. No screenshot, trace, real email, AI, payment or live backend interaction is needed.

## Acceptance

- Browser tests fail on the old automatic wizard/documents redirect, then pass with direct attempt entry.
- Source-based tests that required the superseded redirect are updated, not used as substitutes for executable browser checks.
- The CI browser-regression job uses a pinned compatible Ubuntu runner and locked Playwright dependencies. Existing Python validation remains required.
- Local and CI outcomes are recorded. Mocked browser regression is not claimed as authenticated deployed UAT.
