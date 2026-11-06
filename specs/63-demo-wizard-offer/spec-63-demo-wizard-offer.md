# Spec 63: Existing Offer in the Demo Wizard

- **Related issue:** [#205](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/205)
- **Amends:** [Spec 58](../58-demo-offer-notes/spec-58-demo-offer-notes.md).

Both demo wizard flows offer the same optional existing-offer checkbox, notes, and file input as the documents flow. When checked, completing the wizard requires either a saved PDF, DOCX, or XLSX file of at most 2 MiB or at least 100 trimmed Unicode characters of notes, in addition to the wizard's existing filed-case and role requirements. When unchecked, the additional requirement is removed.

The offer remains temporary to the demo session, survives refresh, and is saved with the demo case on continuation. It is not uploaded or analyzed. Authenticated wizard behavior remains unchanged.
