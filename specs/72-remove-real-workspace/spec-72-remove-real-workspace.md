# Spec 72: Remove Real-Account Workspace Remnants

- **Related issues:** [#263](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/263), [page audit #262](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/262)
- **Amends:** Spec 65 FR-65-04 and Spec 71 requirement 4: remove residual real-account workspace title/identifiers entirely instead of hiding them. Historical specifications remain unchanged.

## Requirements

1. The product HTML contains no `Your case workspace` text, `dashboard-header`, `dashboard-title`, or `dashboard-intro` identifiers or JavaScript references.
2. Keep the existing demo heading capability using demo-only identifiers and an initially hidden demo-only header. Preserve demo navigation, mode selection, assets, attempts, file management, documents and completion screens.
3. Preserve real upload/preparation and wizard routes and controls. The audit's other extra pages are not approved for removal in this change.
4. Keep the account container, APIs, status/error controls, Account tools, start choice, and real attempt workspace. The approved sign-in start-or-attempt behavior is unchanged.
5. Tests reject the old text and nodes even when hidden, verify retained demo-only markup, and verify upload/preparation routes. The executable signed-in browser tests and repository suite must pass.
