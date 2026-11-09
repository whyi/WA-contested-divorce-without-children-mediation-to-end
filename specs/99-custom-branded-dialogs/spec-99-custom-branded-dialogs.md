# Spec 99: Custom-Branded Application Dialogs

- **Status:** Implemented; automated tests passing
- **Supersession:** This additive specification requires application-owned confirmation, notice, and typed-confirmation popups to use a shared Casework-styled dialog instead of browser-native `alert`, `confirm`, or `prompt`. Existing specifications remain unchanged.

## Requirements

- **FR-99-01 — Shared presentation:** Confirmation, informational notice, typed destructive confirmation, and diagnostic-copy interactions use a consistent, responsive Casework dialog with light/dark theme support.
- **FR-99-02 — Safe confirmation:** Confirmation actions are explicit and destructive actions are visually distinct. Cancel, Escape, and backdrop dismissal never confirm an action.
- **FR-99-03 — Typed destructive confirmation:** Irreversible operations require an exact confirmation phrase in a labelled input; the destructive action remains disabled until it matches.
- **FR-99-04 — Accessibility:** The dialog has an accessible title and description, visible keyboard focus, status announcements, and keyboard dismissal. Multiple requests are presented sequentially.
- **FR-99-05 — Diagnostic copying:** Safe diagnostic details are shown in a selectable read-only field; clipboard failure leaves a clear manual-copy fallback.
- **FR-99-06 — No browser-native popups:** The application does not invoke browser-native `alert`, `confirm`, or `prompt`.

## Acceptance criteria

1. All application confirmation, notice and typed-confirmation interactions use the shared styled dialog.
2. Canceling or dismissing a dialog performs no protected mutation.
3. Exact-phrase confirmations cannot continue before the required phrase is entered.
4. Browser tests exercise the shared dialogs and fail if any browser-native popup appears.
