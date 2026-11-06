# Spec 54: Demo Counteroffer and Attempt History

- **Related specification:** [Spec 44: Single-Case Demo Flow](../44-single-case-demo-flow/spec-44-single-case-demo-flow.md)
- **Scope:** The fictional Asset Overview demo response workflow. Existing-offer intake for authenticated cases remains separate.

The demo must not show the existing-offer intake above Asset Overview. A fictional "Offer from the other party" notes panel appears at the bottom of Asset Overview only while "Counteroffer received" is selected. Selecting another response or starting the next attempt hides it. Switching responses on the same page does not erase the notes.

The panel provides notes and one replaceable attachment (PDF, DOCX, or XLSX, at most 2 MiB per file). The file is stored in browser-local IndexedDB, isolated by demo identity, case and attempt. It is not uploaded to the service, analyzed, sent, or used in calculations. Notes and response choices are saved in browser-local case state. The panel must disclose these limits and discourage real case information. Storage and validation failures must be visible; advancing must wait until file storage completes.

The counteroffer panel includes a visible Next action when another attempt is available. It starts the next fictional attempt; Free permits one attempt and Essential permits three. The existing rejected and accepted paths and single-case invariant remain unchanged.

The demo case navigation shows one connected attempt marker per demo entitlement between the case name and the Asset Overview link. Completed markers are gray, the current marker is green, and future markers are empty and unavailable. A distinct outline identifies the attempt currently being viewed. Selecting a completed marker opens its actual browser-local snapshot read-only and focuses a prominent viewing status above the overview; selecting the current marker returns to the current work. Finalizing through the demo's existing "I reviewed and sent" control saves the snapshot before freezing, and advancing records the selected response and counteroffer notes without replacing the frozen proposal values. Current work is retained when navigating to history and restored after a reload. Attachments are also displayed for the associated historical attempt and cannot be changed there.

For legacy demo cases whose ordinal predates saved snapshots, missing history must be indicated as unavailable rather than fabricated. These demo-only snapshots do not change authenticated-case server history or finalization behavior.
