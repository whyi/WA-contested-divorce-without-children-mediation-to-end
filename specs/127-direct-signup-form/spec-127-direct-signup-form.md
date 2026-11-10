# Spec 127: Direct Signup Form from Get Started

- **Issue:** [#384](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/384)
- **Amends:** Spec 97's Account entry requirement only for direct signup entry.
  Login retains the email-first entry. Historical specifications remain unchanged.

## Requirements

1. The signed-out homepage's Get started link opens `/?auth=signup` directly
   on the existing **Sign up for Casework** form. Do not require an initial
   email-and-Continue step.
2. Show the email, email verification, first name, last name, password,
   consent text and signup action immediately. Hide the top Back control
   for this direct entry, including after reload.
3. Signup reached through the login flow retains its Back control and
   carries forward the entered email.
4. The existing-account login action works even before a direct-signup
   visitor enters an email; collect the login email before showing its
   password form. Preserve the existing shortcut for a valid entered email.
5. Email verification, expiration, required fields, consent, authenticated
   navigation and backend authentication are unchanged.

## Verification

- Click Get started and reload at 1280, 390 and 320 pixels. Assert the exact
  heading, complete signup fields, hidden email-entry step and hidden Back.
- Verify signup from login retains Back and the entered email.
- Switch from an empty direct signup to login and enter an email successfully.
- Retain verification, expiration and successful-signup coverage using the
  directly visible signup email field.
