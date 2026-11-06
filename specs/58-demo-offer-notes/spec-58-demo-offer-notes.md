# Spec 58: Demo Offer Notes and Documents Intake

- **Related issue:** [#186](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/186)
- **Amends:** [Spec 57](../57-demo-counteroffer-requirement/spec-57-demo-counteroffer-requirement.md) and [Spec 56](../56-demo-response-controls/spec-56-demo-response-controls.md).

Counteroffer notes qualify for continuation only with at least 100 Unicode characters after trimming leading and trailing whitespace; a successfully stored supported file remains an alternative. Starting a new demo attempt scrolls to the top, and the floating attempt banner is removed.

The documents demo provides an optional existing-offer checkbox. When checked, show a file input and notes field and require either a saved PDF, DOCX, or XLSX file of at most 2 MiB or at least 100 trimmed characters of notes, in addition to the existing document selection requirement. Offer files are stored locally in the browser, isolated by demo identity and case, and notes are stored locally on continuation. They are not sent or analyzed. Unchecking the box removes the additional requirement. Remove the documents demo's Back to Asset Overview button. Real-account behavior remains unchanged.
