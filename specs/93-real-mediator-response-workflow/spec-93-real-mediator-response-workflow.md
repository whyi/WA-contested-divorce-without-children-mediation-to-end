# Spec 93: Complete demo-aligned mediator response workflow

This additive specification amends specs 81, 90 and 92. Prior specifications
remain unchanged.

- Preserve the entire demo response layout below the scenario downloads in real
  Asset Overview, not only the download buttons. Include **I reviewed and sent
  the final documents**, the sent-file list, all three outcome choices, Next,
  rejection choices, plan-limit explanations and the counteroffer panel.
- Replace fictional/sample copy with real-case language. Delivery is performed
  by the user to their mediator; confirmation is a user report, not automatic
  transmission or proof of receipt. Never send directly to the opposing party.
- Require both Word and Excel downloads for the same saved overview revision,
  dates and scenario before enabling delivery confirmation. Changed dates,
  scenario or saved values invalidate prior eligibility. Confirming delivery
  snapshots the proposal profile and freezes its values, dates and scenario.
  Repeated confirmation is idempotent. Draft generation and sent confirmation
  do not consume final-download credits; existing finalization rules remain.
- Persist outcomes, counteroffer notes and attachment links on the server with
  revision checks. Notes autosave; errors retain entered text and show retryable
  failures. Reload restores the same sent/outcome/attachment state. Historical
  responses are viewable but not editable.
- Counteroffer and accepted-offer attachments support PDF, DOCX and XLSX within
  the existing 2 MB/per-case attachment quota. Preserve original names, confirm
  same-name overwrite and use stable upload IDs for retries. Link uploaded files
  atomically to their response; preserve work on storage or cleanup failure.
- Free has one attempt; the paid demo-aligned plan has up to three. Check limits
  on the server before creating a successor. Continuing after a counteroffer
  requires notes or an attachment, carries that context forward and preserves
  the predecessor snapshot. Retrying continuation must not create duplicates.
- Accepted Next opens the existing completion guidance and accepted-document
  attachment controls. Product completion uses the existing reversible accepted
  case closure. Rejection exposes prepare-another-attempt and stop choices;
  confirmed stop uses existing reversible stopped closure. Preserve case data
  and credits; neither is permanent deletion.
- Verify the complete UI, download eligibility, sent confirmation, read-only
  behavior, all response choices, autosave/reload/failure recovery, actual file
  uploads, free/paid limits, successor idempotency and both completion paths.
