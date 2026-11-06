# Spec 46: Document Processing Limits and OCR Support Policy

- **Status:** Implemented for page limit, capability reporting, and user messaging; processing retry ceiling and concurrency limits remain an unset operational gate (see Out of scope)
- **Related issue:** [#135 — Approve document page limits and OCR support policy](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/135)
- **Related issues:** #31 (asynchronous extraction), #32 (consent-based analysis), #125/#141 (failure recovery), #132 (upload limits)
- **Related specifications:** [Spec 07](../07-asynchronous-document-extraction/spec-07-asynchronous-document-extraction.md), [Spec 08](../08-consent-based-document-analysis/spec-08-consent-based-document-analysis.md), [Spec 42](../42-case-attachment-upload-limits/spec-42-case-attachment-upload-limits.md), [Spec 45](../45-failure-messaging-support-escalation/spec-45-failure-messaging-support-escalation.md)
- **Historical specs:** Not edited. This spec is additive and records the behavior the code already enforces.
- **Objective:** State the supported document-processing bounds and capability claims, expose them before analysis, and make every non-completed extraction an explicit, safe per-file state.

## Functional requirements

- **FR-46-01 — Page limit:** A PDF may have at most `MAX_PDF_PAGES` pages; the default is 200. A 200-page PDF is processed; a 201-page PDF is not. The value is configuration (`Settings.max_pdf_pages`, `.env.example`, `docker-compose.yml`) and is the same for every file and every plan; no plan-specific or file-type-specific variant exists.
- **FR-46-02 — Separate from size:** The accepted PDF/DOCX byte size is governed only by `MAX_UPLOAD_BYTES` (2 MiB, Spec 42). A file within the byte limit can still exceed the page limit, and vice versa. DOCX has no page limit.
- **FR-46-03 — Over-limit handling:** Upload does not read page counts. An over-limit PDF within the size and quota limits is stored. Its extraction job ends `needs_attention` with error code `page_limit_exceeded`, no extracted text is saved, and the file is not eligible for AI analysis. The PDF-to-DOCX conversion route rejects it with the same limit.
- **FR-46-04 — OCR unsupported:** OCR is not configured. A PDF with any page lacking selectable text ends `needs_attention` with `ocr_required`. The file is never reported as analyzed. The user path is to supply a text-based (or manually transcribed alternate-text) version of the document; no OCR vendor, languages, or image-text extraction is offered or implied.
- **FR-46-05 — Encrypted PDFs:** A password-protected PDF ends `needs_attention` with `password_protected`; the service never asks for or applies a password. The user must remove protection and upload an unprotected copy.
- **FR-46-06 — Other states:** Unreadable or zero-page PDFs use `unreadable_file`; other extensions use `unsupported_file`. Supported formats remain PDF and DOCX only.
- **FR-46-07 — Visible before analysis:** `GET /api/v1/materials/config` additionally reports `max_pdf_pages` (the server value) and `ocr_supported` (always `false`). The materials page states the page limit, that scanned PDFs are not read, and that encrypted PDFs must be unprotected first. The analysis-selection list gives a specific message for `page_limit_exceeded`, `ocr_required`, and `password_protected`.
- **FR-46-08 — Stage separation:** Storage, extraction, and consented AI analysis remain distinct (Specs 07/08). Hitting a limit never withdraws storage and never starts or implies analysis; a `needs_attention` file cannot be selected for analysis.
- **FR-46-09 — Existing runtime bounds:** Only these bounds are currently enforced and are the supported claim: extraction job lease of 10 minutes, and DOCX-to-PDF rendering timeout `CONVERSION_TIMEOUT_SECONDS` (default 90).

## Acceptance criteria

- 200 pages are extracted; 201 pages produce `page_limit_exceeded` (default settings), and a lower configured value is honored.
- A job with an over-limit PDF finishes `needs_attention`/`page_limit_exceeded` and saves no extraction.
- Scanned (`ocr_required`) and encrypted (`password_protected`) PDFs end `needs_attention`.
- `materials/config` returns `max_pdf_pages` and `ocr_supported: false`; the page text and analysis messages match.

## Out of scope / not decided

Product approval of the numbers, a per-job retry ceiling, per-case/job concurrency limits, an extraction processing-time SLA, OCR, embedded-image text, and plan-based variants are not implemented or promised. They remain an operational decision gate that must be resolved separately before any such claim is made.
