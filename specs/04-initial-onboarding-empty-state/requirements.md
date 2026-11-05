# Specification 04: Active-Case Dashboard and Case Creation Flow

- **Status:** In progress
- **Related specifications:** [Spec 02: Overall Requirements](../02-requirements/spec-02-overall-requirements.md), [Spec 03: Authentication](../03-authentication/spec-03-authentication.md)
- **Objective:** Give a signed-in user a visual overview of active cases and a plan-aware, two-path flow for starting a case.
- **Scope:** This specification defines the case dashboard, case summaries, active-case capacity, new-case dialog, and routing into document-first or wizard preparation. It does not define document extraction, wizard fields, or later case-processing steps.

## 1. User Flow

1. A user signs in successfully.
2. The application opens the user's account page.
3. The application loads the case status for the authenticated account.
4. The account page shows active cases as large, rounded-square tiles. Each tile has a concise case label and the latest negotiation attempt; selecting a tile reopens that case's saved preparation path, or its case workspace if no preparation path is recorded.
5. A **“+ Start a new case”** tile appears while the account has remaining active-case capacity. Selecting it opens an in-page dialog with an optional case label and two choices:
   - **“I have documents”** — creates a case and starts the document-first path.
   - **“Guide me step by step”** — creates a case and starts the wizard path.
6. When the plan's active-case limit is reached, replace the enabled creation tile with a disabled tile that explains the limit and links to plan comparison. The server independently enforces the limit.
7. The plan catalog currently allows 1 active case on Free, 3 on Essential, 10 on Plus, and unlimited active cases on Pro. The dashboard reads these values from the server; it must not duplicate them as client-side authority.

## 2. Dashboard and Capacity Behavior

- Active cases are presented as tiles; the same dashboard and case-creation affordance are shown whether the account has zero or multiple cases.
- Existing case tiles show a useful label (for example, `XYZ vs ABC`) and the current attempt (for example, `2nd Attempt`) without exposing case contents in the dashboard.
- The new-case tile is visually prominent and opens an in-page dialog rather than navigating to a separate onboarding chooser.
- When capacity remains, the dialog offers document-first and wizard choices. The selected mode and case ID remain associated throughout navigation and on dashboard return.
- When at capacity, the creation tile is visibly and semantically disabled, and an upgrade/plan-comparison action is available.
- The empty state must not imply that signing in alone grants access to a case or verifies legal identity or authority.
- Do not show case data belonging to another account.
- If case status cannot be loaded, show an actionable error and a retry option. Do not treat a failed or unauthorized status request as an empty account.

## 3. Status API

The account page needs an authenticated status endpoint to render the case tiles and plan capacity.

- **Proposed route:** `GET /api/v1/dashboard/status`
- The endpoint must derive the account identity from the validated authentication context; it must not accept a client-supplied account ID as authority.
- It must return only active cases visible through an active case-membership grant, with each case's ID, status, safe display title, starting workflow mode (if any), and latest attempt ordinal.
- It must return the user's active owned-case count, active-case limit, and plan name for capacity display. A `null` active-case limit means unlimited.
- Unauthorized requests must fail without disclosing whether another account has cases.

Example response for an account with no active case records:

```json
{
  "status": "success",
  "data": {
    "has_cases": false,
    "case_count": 0,
    "active_case_count": 0,
    "active_case_limit": 1,
    "plan_name": "Free",
    "cases": []
  }
}
```

`has_cases` and `case_count` must match the returned active case summaries.

## 4. Routing and Case Creation

- The document-first and wizard choices create a case through the authenticated case-creation endpoint, with the selected workflow and optional label saved to case metadata.
- Reopening a case tile routes to that case's saved workflow and carries its case ID; it must not create another case.
- Document imports started from a dashboard-created case attach to that case. The legacy document-import path that creates a case itself must also enforce the same active-case limit.
- A new case must be created only in the context of the authenticated account and according to the application's case-authorization and plan-limit policies.
- Refreshing the account page or retrying a request must not create duplicate cases.
- Navigation away from either path and back to the account page must not expose another account's data.
- The upload and wizard workflows themselves are specified separately; this specification does not authorize enabling case or document APIs without their required authentication and case-level authorization.

## 5. Error and Loading States

- While status is loading, show a clear loading state rather than briefly displaying the empty state.
- If the request fails, show a non-sensitive error and allow the user to retry.
- If the session is expired or invalid, follow the application's sign-in flow; do not show account or case status.
- Do not silently convert server, network, or authorization errors into `has_cases: false`.

## 6. Accessibility and Responsive Behavior

- Case tiles and dialog choices must be keyboard accessible and have accessible names matching their visible labels.
- Visual prominence must not rely on color alone.
- Tiles and dialog choices must remain usable on narrow/mobile screens without horizontal scrolling or obscured text.

## 7. Acceptance Criteria

1. After successful sign-in, the user lands on their account page.
2. The dashboard displays existing case tiles with their labels and current attempt ordinals.
3. The new-case tile opens an in-page dialog; either mode choice creates one case and continues with that case ID.
4. Tile capacity matches the active plan, and both case creation and legacy document-import creation reject over-limit attempts server-side.
5. A status-loading or status-error condition never appears as a successful empty dashboard.
6. An unauthenticated user cannot retrieve account status, and a user cannot learn another account's case summaries or case count.
7. Retrying or reloading the dashboard does not create cases; reopening a tile does not duplicate its case.

## 8. Out of Scope and Follow-up Decisions

- Exact upload file types, limits, storage, malware scanning, extraction, and review UX.
- Wizard fields, validation rules, and step sequence. Wizard answers and attachments remain browser-local until a separately specified secure persistence workflow is implemented.
- Case lifecycle actions such as archiving/finalizing and removing a case from the active-case count.
- API versioning and final response/error schema must follow the application's established API conventions when implemented.
