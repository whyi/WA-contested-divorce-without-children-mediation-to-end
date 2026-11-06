# Spec 56: Demo Response Controls

- **Related issue:** [#181](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/181)
- **Amends:** [Spec 40](../40-rejection-stop-completion/spec-40-rejection-stop-completion.md), FR-40-06, only for the demo response controls.
- **Also amends:** [Spec 55](../55-demo2-start-choice/spec-55-demo2-start-choice.md) re-entry behavior for Demo 2.

The demo accepted-offer completion page offers Back to mediation, returning to the same demo case. It does not show the redundant Back to your case or a nonfunctional completion action. Authenticated case completion controls and the existing direct rejection-completion routes remain unchanged.

The demo rejected-offer response offers preparation of another attempt when permitted, but no fictional-stop button. Past attempt markers display "Viewing Nth Attempt read-only snapshot." Actual historical snapshots remain read-only.

Every homepage entry to Demo 2 opens the preparation-path choice, including when a browser-local case already exists. Selecting a path opens that path for the existing case without replacing its data or creating a second case. Demo 1 re-entry remains unchanged.
