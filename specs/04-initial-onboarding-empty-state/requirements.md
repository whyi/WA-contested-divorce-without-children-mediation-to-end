# Specification 04: Initial Onboarding Empty-State Dashboard and Dual-Path Routing

- **Status:** Draft
- **Related specifications:** [Spec 02: Overall Requirements](../02-requirements/spec-02-overall-requirements.md), [Spec 03: Authentication](../03-authentication/spec-03-authentication.md)
- **Objective:** Specify the account-page experience after sign-in when the account has no case records, with two clear starting paths: upload existing case materials or enter information through a guided wizard.
- **Scope:** This specification defines the empty account state and routing into the two preparation modes. It does not define the upload/extraction workflow, wizard questions, or later case-processing steps.

## 1. User Flow

1. A user signs in successfully.
2. The application opens the user's account page.
3. The application loads the case status for the authenticated account.
4. If the account has no case records, the account page shows an onboarding empty state with two prominent, equally discoverable actions:
   - **“I already have case materials, so I'll upload them”** — starts the existing-materials preparation path.
   - **“Guide me through the wizard step by step”** — starts the guided wizard path.
5. Selecting an action begins the corresponding path for a new case. Both paths must retain the association with the signed-in account and lead into the case-information workflow.
6. If the account already has case records, the account page shows the user's existing cases instead of the first-time empty state.

## 2. Empty-State Behavior

- The empty state is shown when the authenticated account has zero case records (`case_count == 0`).
- The two actions must be visually prominent and presented as the primary choices on the page; neither may be hidden behind a menu or secondary navigation.
- The displayed English labels must match the text specified above.
- The actions must clearly communicate their different purposes: organizing materials the user already has, or entering information step by step.
- The empty state must not imply that signing in alone grants access to a case or verifies legal identity or authority.
- Do not show case data belonging to another account.
- If case status cannot be loaded, show an actionable error and a retry option. Do not treat a failed or unauthorized status request as an empty account.

## 3. Status API

The account page needs an authenticated status endpoint to decide whether to show the empty state or the existing-case view.

- **Proposed route:** `GET /api/v1/dashboard/status`
- The endpoint must derive the account identity from the validated authentication context; it must not accept a client-supplied account ID as authority.
- It must return only the authenticated account's case count/status and no case contents.
- Unauthorized requests must fail without disclosing whether another account has cases.

Example response for an account with no case records:

```json
{
  "status": "success",
  "data": {
    "has_cases": false,
    "case_count": 0
  }
}
```

For an account with one or more case records, `has_cases` must be `true` and `case_count` must reflect the number of cases visible to that account under the applicable authorization rules.

## 4. Routing and Case Creation

- The upload action must route into the existing-materials preparation flow for a new case.
- The wizard action must route into the guided-entry flow for a new case.
- A new case must be created or initialized only in the context of the authenticated account and according to the application's case-authorization policy.
- Refreshing the account page or retrying a request must not create duplicate cases.
- Navigation away from either path and back to the account page must not expose another account's data.
- The upload and wizard workflows themselves are specified separately; this specification does not authorize enabling case or document APIs without their required authentication and case-level authorization.

## 5. Error and Loading States

- While status is loading, show a clear loading state rather than briefly displaying the empty state.
- If the request fails, show a non-sensitive error and allow the user to retry.
- If the session is expired or invalid, follow the application's sign-in flow; do not show account or case status.
- Do not silently convert server, network, or authorization errors into `has_cases: false`.

## 6. Accessibility and Responsive Behavior

- Both actions must be keyboard accessible and have accessible names matching their visible labels.
- Visual prominence must not rely on color alone.
- The two actions must remain usable on narrow/mobile screens without horizontal scrolling or obscured text.

## 7. Acceptance Criteria

1. After successful sign-in, the user lands on their account page.
2. With zero cases, the page displays both exact English action labels as prominent choices.
3. Selecting the upload action starts the existing-materials path; selecting the wizard action starts guided entry.
4. With one or more authorized cases, the page shows existing cases and does not present the first-time empty state as if the account had no cases.
5. A status-loading or status-error condition never appears as a successful empty state.
6. An unauthenticated user cannot retrieve account status, and a user cannot learn another account's case count.
7. Retrying or reloading the account page does not create duplicate cases.

## 8. Out of Scope and Follow-up Decisions

- Exact upload file types, limits, storage, malware scanning, extraction, and review UX.
- Wizard fields, validation rules, save behavior, and step sequence.
- The existing-case dashboard layout and case lifecycle.
- Whether a case with no uploaded documents should count as an empty account. This draft uses **zero case records** as the empty-state condition; product requirements should clarify this if “no case materials” is intended to mean no documents even when a case record already exists.
- API versioning and final response/error schema must follow the application's established API conventions when implemented.
