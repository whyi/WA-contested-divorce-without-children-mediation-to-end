# Spec 61: Demo Rejection and Attempt Limits

- **Related issue:** [#193](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/193)
- **Amends:** [Spec 56](../56-demo-response-controls/spec-56-demo-response-controls.md) and [Spec 60](../60-demo-attempt-limit/spec-60-demo-attempt-limit.md).

Use a smaller, less prominent heading in the attempt-limit dialog. For a rejected offer, label the action "Make 2nd attempt", "Make 3rd attempt", and so on, based on the current attempt. Within the demo tier's allowance, the action starts the next attempt. At the limit it remains clickable, uses the same muted appearance as the validated counteroffer action at the limit, and opens the same upgrade dialog. Do not start another attempt at the limit. Past snapshots remain read-only.
