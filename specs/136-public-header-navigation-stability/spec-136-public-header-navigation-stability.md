# Spec 136: Stable Public Header Navigation

- **Issue:** [#417](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/417)
- **Amends:** Specs 107 and 108 for public-page Get started visibility and
  navigation transitions. Their authenticated-state and protected-content
  requirements remain in force. Spec 126's homepage destination and Spec 127's
  visible control order remain unchanged.

## Requirements

1. Keep the public header's visible controls in a stable order and position
   while navigating among the homepage, Pricing, login, and Get started views.
   Keep the same-page session check from moving or flashing adjacent controls.
2. Show Get started on public pages only after sign-out has been confirmed with
   HTTP 401 or a successful logout response. After confirmation, the current tab
   may reuse the verified signed-out result on later public navigations so the
   control is present immediately. The hint must never reveal Account, Your
   case, Logout, or protected case content.
3. Keep Get started unavailable while no signed-out result has been confirmed,
   including during the first pending check and after its failure when there is
   no prior confirmed sign-out. A verified server session or later
   authenticated response clears any cached signed-out result and keeps Get
   started hidden.
4. Support Get started on public homepage, Pricing, login/signup/authentication,
   and demo pages after confirmed sign-out. Keep its existing destination at
   `/?auth=signup`.
5. Clicking the header link for the page already being shown does not reload
   the document. Preserve normal link behavior for modified clicks and keep
   navigation to other pages unchanged.
6. Preserve signed-in control visibility, authentication checks, and all
   protected-page routing and authorization behavior.

## Verification

- Exercise navigation between `/`, `/pricing`, `/?auth=login`, and
  `/?auth=signup` from each public page with the session response delayed.
- Verify the first visit keeps Get started hidden until HTTP 401, then verify
  later same-tab navigations show it before the next status response. Verify a
  successful logout also makes it available immediately.
- Compare visible header controls and their geometry across destinations at
  desktop and mobile widths.
- Verify same-page clicks do not navigate the main frame; modified clicks
  retain native browser behavior.
- Verify session failures without a prior 401 keep Get started hidden, and a
  verified signed-in session suppresses it and clears the signed-out hint.
