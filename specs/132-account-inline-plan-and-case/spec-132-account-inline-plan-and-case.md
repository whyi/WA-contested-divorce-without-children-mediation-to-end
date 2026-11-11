# Spec 132: Inline Account Plan and Case

- **Issue:** [#405](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/405)
- **Amends:** Specs 129 and 130 for Account presentation only. Supersede the
  separate plan, case, and permanent-deletion cards; retain historical specs.

## Requirements

1. Keep the existing Account information card and profile rows. Immediately
   below Password, add Your plan with the current plan and Upgrade on the right.
   Do not hardcode a paid plan for free accounts.
2. Move the existing Your case status and actions into the next row of that
   same card. Preserve active/closed visibility, unnamed case presentation,
   destinations, export, closure, and reopening behavior.
3. Remove standalone plan and case cards. Preserve Upgrade expansion and
   checkout in the inline plan row. Keep normal plan presentation on one line;
   show expanded package information and explicit loading errors when needed.
4. Remove the permanent-deletion card and its heading. Place the red
   Permanently delete my account button below Account information.
5. Preserve the existing deletion dialog, authentication/CSRF checks, validation,
   duplicate-submit prevention, retry, Cancel/Escape behavior, and focus handling.
6. Preserve theme styling and usable desktop/mobile layouts without horizontal
   page overflow. Case actions may wrap on narrow screens.

## Verification

- Verify profile, plan, and case row order and absence of standalone cards.
- Check Free and Essential labels, Upgrade alignment, package expansion,
  active/closed cases, and explicit billing errors.
- Retain deletion dialog and case-action regression coverage.
- Check 1280, 800, 390, and 320 pixel viewport widths.
