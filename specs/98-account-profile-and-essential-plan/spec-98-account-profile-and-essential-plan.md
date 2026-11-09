# Spec 98: Account Profile and Essential Plan Label

- **Status:** Implemented; automated tests passing
- **Related specifications:** [Spec 67: Account Plan and Upgrade Action](../67-account-plan-and-upgrade/spec-67-account-plan-and-upgrade.md), [Spec 97: Minimal Account Entry, Verified Signup and Visible Logout](../97-email-first-signup-and-logout/spec-97-email-first-signup-and-logout.md)
- **Supersession:** This additive specification amends Spec 67 FR-67-01 and acceptance criterion 1 by naming the paid plan **Essential** and adds the account identity details below. Existing specifications remain unchanged.

## Requirements

- **FR-98-01 — Account identity:** The signed-in Account area shows the authenticated account's email, first name and last name. Missing names are shown as “Not provided.”
- **FR-98-02 — Scoped profile API:** `GET /api/auth/account` requires authentication and returns only the current user's email and names. It does not expose credentials, tokens or another user's profile.
- **FR-98-03 — Essential label:** The trusted `paid` entitlement is displayed as **Essential plan**; `free` remains **Free plan**. Essential names the paid entitlement in the interface and does not imply a recurring subscription or a separate subscription tier.
- **FR-98-04 — Separate credits:** Plan status and attempt-credit balance remain separate. Existing upgrade and one-time credit purchase behavior is preserved.
- **FR-98-05 — Local test seed:** The isolated local seed may fill missing names on its fictional Free and Essential accounts, but must preserve existing names, passwords, account data and case data.

## Acceptance criteria

1. An unauthenticated profile request is rejected; an authenticated request returns only its user's email and names.
2. The Account area renders the profile and labels a server-reported paid entitlement “Essential plan.”
3. Existing free-versus-paid entitlement behavior and credit purchase controls continue to work.
4. Local account seeding is idempotent and does not replace existing identity or case data.
