# Spec 17: Accessible, Persistent Dark Theme

- **Status:** Draft
- **Related issue:** [#66 — Add an accessible, persistent dark theme](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/66)
- **Objective:** Provide a consistent, accessible dark appearance while preserving the existing light appearance and allowing users to choose Light, Dark, or System.
- **Scope:** Theme selection, system preference detection, persistence of an explicit preference, consistent theme tokens across the application, and accessible rendering in both themes. This is a presentation preference; it does not change application data or behavior.

## 1. Theme Selection and Preference

- **FR-17-01 — Available modes:** Provide a labeled, keyboard-operable control with the three choices **Light**, **Dark**, and **System**. Clearly expose the selected choice to assistive technology.
- **FR-17-02 — Initial mode:** When the user has not saved an explicit choice, use the operating-system color preference when available. If it is unavailable, use Light.
- **FR-17-03 — System mode:** In System mode, follow changes to the operating-system color preference while the application is open. Do not persist the resolved Light/Dark value as though it were an explicit choice.
- **FR-17-04 — Explicit preference persistence:** Persist a user-selected Light or Dark choice across page reloads and navigation using browser-local preference storage. Persist System as a distinct choice. Do not send theme preferences to the application API, database, or an external provider.
- **FR-17-05 — Preference recovery:** If browser preference storage is unavailable or contains an unsupported value, continue using the system preference (or Light when unavailable) without preventing the application from loading. Do not interpret invalid stored values as a user selection.
- **FR-17-06 — No-theme-change behavior:** Changing themes must not modify, clear, or submit case data, authentication state, consent, or other application preferences.

## 2. Consistent Application Styling

- **FR-17-07 — Shared theme tokens:** Define reusable color tokens for page and surface backgrounds, primary and secondary text, borders, links, buttons, form controls, status messages, overlays, and charts. Use the tokens consistently rather than adding unrelated per-component overrides.
- **FR-17-08 — Application coverage:** Apply the selected theme consistently to the landing and authentication screens, dashboard, wizard, fictional demos, shared dialogs, and interactive controls.
- **FR-17-09 — Component states:** Provide distinguishable and legible hover, keyboard-focus, selected, disabled, validation-error, warning, and success states in both themes. Do not communicate state by color alone.
- **FR-17-10 — Charts and data displays:** Ensure chart series, markers, axes, legends, tables, and status indicators remain distinguishable and readable in both themes. Preserve existing chart meaning and interaction.
- **FR-17-11 — Existing behavior:** Theme styling must not change page structure, navigation, validation, feature availability, demo-only boundaries, authorization, consent, or data handling.
- **FR-17-12 — No external dependency:** Implement theme support without introducing a UI framework, remote theme service, or external runtime dependency.

## 3. Accessibility and Rendering

- **FR-17-13 — Contrast:** Meet WCAG 2.2 AA contrast requirements for text, controls, boundaries, and state indicators in both themes, including normal text contrast of at least 4.5:1 and large text contrast of at least 3:1.
- **FR-17-14 — Keyboard and focus:** Theme selection and every affected interactive control must remain keyboard-operable, with a clearly visible focus indicator in both themes.
- **FR-17-15 — Reduced motion:** If theme changes animate, respect `prefers-reduced-motion` and provide an equivalent non-animated transition.
- **FR-17-16 — Initial paint:** Resolve the saved preference or system preference before displaying themed application content, preventing a visible flash of the wrong theme on page load.
- **FR-17-17 — System preference updates:** In System mode, respond to operating-system preference changes without requiring a page reload. Do not override a saved explicit Light or Dark choice when the system preference changes.

## 4. Testing

- **FR-17-18 — Mode behavior tests:** Test explicit Light, explicit Dark, default System behavior, and changes to the system preference while System mode is active.
- **FR-17-19 — Persistence tests:** Test that each selected mode survives reload/navigation as expected and that invalid or inaccessible stored preference data does not prevent rendering.
- **FR-17-20 — Theme coverage tests:** Test representative landing/authenticated/demo screens and shared controls in both resolved themes, including key text, controls, error/status states, and chart/data-display styling.
- **FR-17-21 — Regression tests:** Verify that theme selection does not cause API requests or alter case data, authentication, consent, or demo behavior.

## 5. Acceptance Criteria

1. Users can select Light, Dark, or System using a pointer or keyboard, and assistive technology can identify the selected mode.
2. With no saved choice, the application follows the operating-system preference and defaults to Light when that preference is unavailable.
3. Explicit Light, Dark, and System choices persist across reloads and navigation; System mode follows operating-system preference changes while open.
4. The selected theme is consistently applied across the landing and authentication screens, dashboard, wizard, fictional demos, shared dialogs, controls, and charts.
5. Text, controls, focus indicators, and interaction states remain readable and distinguishable in both themes and meet the specified WCAG 2.2 AA contrast thresholds.
6. The initial page render uses the resolved theme without a visible flash of an incorrect theme.
7. Theme preference failures do not block application loading, and changing themes does not alter application data, security boundaries, or existing behavior.
8. Automated tests cover mode selection, system preference changes, persistence and recovery, representative theme rendering, and regression boundaries.
