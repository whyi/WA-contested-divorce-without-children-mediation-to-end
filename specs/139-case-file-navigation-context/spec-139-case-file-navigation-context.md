# Spec 139: Case File Navigation Context

- **Amends:** Spec 79, Real Case Workspace Navigation, and Spec 109,
  Accepted Completion Progress. Historical specifications remain unchanged.

## Requirements

- Remove the Asset Overview navigation button from shared case navigation on
  attempt, case file management, and accepted completion pages. Attempt circles
  remain the way to navigate to an attempt.
- When entering case file management from accepted completion, keep the
  confirmed Offer Accepted circle green and selected rather than selecting the
  latest attempt. It remains navigable back to completion.
- When entering file management from an explicitly selected attempt, preserve
  that selection. A file-page reload preserves the selected context.
- Clicking the current Case file management link does not reload the page.
  Preserve modified-click and new-tab behavior.
- Preserve case ownership, accepted-offer verification, closed-case context,
  attempts, and file operations. A navigation parameter alone cannot establish
  acceptance. Apply the same navigation and selection behavior to fictional
  demos, with attempts navigable from demo file management.

## Verification

Test both accepted-offer implementations, open and closed cases, reload,
attempt and completion navigation, no-op self-click, and demo navigation.
