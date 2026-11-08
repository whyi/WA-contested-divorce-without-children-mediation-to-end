# Spec 76: Remove the Legacy Negotiation Planner Page

- **Status:** Specified; removal and regression tests in the same pull request
- **Amends:** Specs 65, 70, 71, 72, 73 and 74 where they require real-account entry, documents Continue, or wizard completion to open the legacy negotiation planner. Historical specifications remain unchanged.
- **Objective:** Delete the technical negotiation-planning page, not merely hide or collapse it.

## Removal contract

1. Remove the real-account **Negotiation attempts** page and its HTML, page-specific styles, state, event handlers, JSON ledger/scenario inputs, AI-ranking consent UI, scenario calculation/selection controls, and dependent proposal-editor UI.
2. Remove all entry calls to that page. An active case opens its saved documents or wizard preparation route. A case without a saved workflow presents the existing path choice without creating another case.
3. Saving the offer choice remains on the documents screen. Saving wizard information remains on the wizard; it no longer automatically creates an attempt or opens the deleted page. Make the save-only labels explicit.
4. Preserve case export, reversible closure and immediate permanent deletion under **Account**. Preserve materials, wizard drafts, existing offers, purchased credits and server-side attempt data. No API or database data is removed.
5. Preserve fictional demo assets, scenario selection, attempts, sample downloads and completion routes. Do not substitute fictional demo data for a real case.
6. Preserve existing accepted-offer completion links, attachment upload, server verification and case completion independently of the deleted editor.
7. Historical specifications are retained for traceability; their old page requirements are superseded by this specification. Old static tests requiring the deleted controls are replaced by deletion and routing regressions, while backend tests remain.

## Explicit behavior change

Real-account scenario calculation, proposal editing/generation and negotiation-attempt navigation are no longer exposed by this frontend. This change does not introduce a replacement negotiation screen. The backend and saved data remain available for a future separately specified interface.

## Verification

- Assert absence of the deleted page title, technical labels, IDs and loader, including hidden DOM.
- Exercise login/refresh for documents, wizard and unassigned workflows; saving must never redirect to the removed page.
- Exercise case-management controls in Account, both demos and accepted-offer completion without script errors or unmocked API requests.
- Retain backend authorization, persistence, calculation and lifecycle tests.
