# Spec 62: Demo Completion and Refresh

- **Related issue:** [#195](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/195)
- **Amends:** [Spec 56](../56-demo-response-controls/spec-56-demo-response-controls.md) and [Spec 59](../59-ephemeral-demo/spec-59-ephemeral-demo.md), only for the demo.

The accepted-offer demo page offers "I'm done!" beside Back to mediation. The action asks for confirmation that the demo case will become read-only for the rest of the demo. No cancels; Yes completes and locks the demo case. Case review and file downloads remain available, but changes and new attempts are blocked. Restarting from the home page creates a fresh demo.

Refreshing a demo does not restart it or discard its saved session state. Demo state is temporary to the browser tab; real-account behavior and case retention remain unchanged.
