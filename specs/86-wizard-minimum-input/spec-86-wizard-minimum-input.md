# Spec 86: Reactive wizard completion with minimum input

This additive specification amends the wizard completion gate in spec 85 and prior
guided-intake specifications. Existing specifications remain unchanged.

- Completion requires a filed case, a selected Petitioner/Respondent role, known
  valid marriage and petition-filing dates, and at least one asset or debt with a
  nonblank category or description. A blank newly added row is not sufficient.
  Financial estimates and other dates remain optional; do not demand unrelated
  fields, evidence attachments, issues, or agreements.
- Re-evaluate the same predicate on every date/unknown toggle, financial field
  input, add/remove action, base-answer change, and restored draft. Minimum input
  immediately enables the button; removing required input disables it again.
- Real-account completion additionally requires a successfully loaded server
  draft. Preserve explicit loading/save/conflict errors and editable retries.
- Remove the obsolete below-button sentence about filed status and role, its
  DOM node, and its accessibility reference.
- Use the same minimum-input gate in demos and real-account onboarding. Keep
  current destination behavior: demo completion opens its case overview; real
  completion saves in place. Partial draft autosaving remains available.
- Verify both asset/debt rows, role choices, unknown dates, deletion of the last
  row, draft restoration, real save failures, and real draft loading failures.
