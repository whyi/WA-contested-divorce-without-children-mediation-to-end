# Spec 82: Restore optional offer input on documents entry

This specification amends spec 81's removal of the document-mode offer checkbox.
The old materials-workflow page remains deleted; its replacement continues to use
the shared demo document-selection layout.

- Immediately below the document-page introduction, show a checkbox asking whether
  the other party has already made an offer or counteroffer.
- Only while checked, show the existing offer editor: text notes, optional PDF/DOCX
  upload or existing document selection, and the Save offer details button.
- Accept text, a file, or both through the existing authenticated offer API. Do not
  create a new negotiation attempt or start AI processing.
- Restore the saved checkbox state and details on reload. Unchecking unsaved input
  hides the editor while preserving the local draft. Removing a saved offer requires
  confirmation; cancellation or save failure restores the checked visible state.
  Removing the offer association does not permanently delete uploaded files.
- Next saves a checked offer before importing selected case materials and navigating.
  Validation or storage failure keeps the user on the page with explicit errors.
- Offer-loading failures are visible outside the hidden panel and offer retry.
  Do not enable offer editing or Next while the saved offer state is unknown.
- Keep wizard offer input, upload quotas, retry identities, and server access checks
  unchanged. Do not bring back the deleted upload interstitial or analysis UI.
