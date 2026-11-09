# Spec 90: Interactive real-case trend dates and visible scenario ideas

This additive specification amends specs 80 and 81's real Asset Overview
interaction. Prior specifications remain unchanged.

- The real Asset Trend chart supports mouse/touch pointer date selection like
  the demo: click near an endpoint or drag it to change the start/division date.
  Snap pointer selection to saved snapshot or milestone dates; do not invent
  unsaved balances. Pointer capture keeps dragging functional outside the plot,
  and pointer cancellation ends the gesture.
- Use the same timeline domain for the plotted points, pointer selection and
  selected-date band. Display the band and both endpoint lines. The first range
  defaults to earliest/latest saved dates rather than empty inputs. A single
  saved date supports a same-date comparison; with no dates, disable date input.
- Exact date inputs remain available and update the chart and scenario cards.
  Disable date gestures while editing/saving balance-sheet values.
- Always display the three shared higher/even/lower-share scenario idea cards.
  With complete explicitly saved endpoint balances, calculate from real cents:
  preserve each party's starting balance and split the combined net change
  using the proposed 55%, 50% or 45% share. Selectable options update locally.
- When dates or amounts are missing/invalid, show **Unavailable** values and
  disabled options with a visible explanation, not an empty panel, fictional
  demo values, interpolated figures, or zero substitutes.
- Verify actual mouse clicks and drag gestures, exact date changes, recalculated
  dollar amounts for all three shares, missing data and unchanged case storage.
