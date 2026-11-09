# Spec 85: Unboxed start pages and a clean guided wizard

This additive specification amends spec 84's starting-page presentation and
spec 79's case navigation on guided onboarding. Existing specifications remain
historical records.

- Render starting-point pages using the document page's centered 760px content
  width, generous top/bottom spacing, and large responsive serif heading.
  Remove both the outer account panel and the inner starting-page card treatment:
  no enclosing border, background box, rounding, or shadow. Keep the selectable
  documents/guided option cards and existing copy.
- Apply the same presentation to new-case, existing-case, and demo starting pages.
  They remain normal pages, not dialogs.
- Guided onboarding starts at its own **Guided intake preview** content. Remove the
  wrapper's **Your next step**, **Start with guided entry**, description, and preview
  warning markup and related script/style references rather than hiding them.
- Do not show attempt navigation, Asset Overview, or Case file management above
  the wizard. Load saved wizard intake and optional existing-offer details directly;
  do not fetch a case workspace just to mount negotiation navigation.
- Retain questionnaire controls, saved draft/reload, explicit save failures, and the
  optional offer editor below the wizard. Asset Overview and file-management pages
  continue to show their own case navigation.
- Verify unboxed start-page styles against the document page at desktop/mobile
  widths and wizard entry without the deleted preamble or case navigation.
