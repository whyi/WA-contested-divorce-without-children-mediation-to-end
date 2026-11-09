# Spec 80: Theme Selector on Every Page

- **Status:** Specified; implementation and regression tests in the same pull request
- **Related issue:** [#331 — Keep the theme selector visible on every page](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/331)
- **Amends:** Spec 17, adding a page-availability requirement without changing its theme modes, preference storage, or rendering behavior. Historical specifications remain unchanged.
- **Objective:** Make the existing Theme selector consistently available in the shared top-right header, whether or not a visitor is signed in.

## Requirements

1. Keep the labeled Theme selector visible in the shared application header on every user-facing page, including the public homepage, login and other authentication pages, signed-in views, demos, and completion pages.
2. Do not condition selector visibility on authentication state, route, or navigation state.
3. Keep the selector usable at desktop and mobile widths and preserve its keyboard operation and accessible label.
4. Preserve the existing System, Light, and Dark choices, saved preference behavior, system preference handling, and theme application.
5. Theme selection must not change authentication, navigation, case data, or other application behavior.

## Acceptance Criteria

- A signed-out visitor can see and operate the Theme selector on the public homepage and authentication screens.
- The selector remains visible on representative signed-in, demo, and completion views.
- Responsive layouts do not clip or hide the selector; keyboard and accessible-name checks pass.
- Regression tests confirm existing preference persistence and System mode behavior are unchanged.
