# Spec 59: Ephemeral Demo Sessions

- **Related issue:** [#189](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/189)
- **Amends:** Demo persistence and reload behavior in Specs 44, 54, 55, 57, and 58.

Both demos start with the preparation choice and a fresh first attempt whenever entered from the home page. Refreshing any demo page clears that demo's temporary case, files, and attempt history and returns to the preparation choice. Prior attempts remain available as read-only snapshots during an uninterrupted demo run.

Demo data is temporary to the browser tab and is not restored from legacy persistent demo storage. The demo wizard retains its answers only while its page is open. If temporary storage is unavailable or full, report the error rather than claiming success. Authenticated case and wizard persistence, and legacy browser data, remain unchanged.
