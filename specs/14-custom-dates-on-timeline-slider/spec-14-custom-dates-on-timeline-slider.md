# Spec 14: Custom Dates on the Timeline Slider

- **Status:** Implemented
- **Related issue:** [#59 — Include custom milestone dates in the year slider](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/59)
- **Related specifications:** [Spec 10: Mock Asset-Analysis Dashboard](../10-mock-asset-analysis-dashboard/spec-10-mock-asset-analysis-dashboard.md), [Spec 11: Relationship Milestone Timeline](../11-relationship-milestone-timeline/spec-11-relationship-milestone-timeline.md), and [Spec 13: Editable Asset Comparison](../13-editable-asset-comparison/spec-13-editable-asset-comparison.md)
- **Objective:** Include user-defined dates as selectable stops in the asset timeline slider and show a useful comparison snapshot at the exact selected date.
- **Scope:** Timeline slider stops, date-based sample interpolation, explicit interpolation notices, editing an interpolated point, and local chart/table refresh. No real case data or persistence is involved.

## 1. Timeline Stops and Navigation

- **FR-14-01 — Annual and milestone stops:** Retain all six annual sample stops and add one stop for each distinct available relationship milestone date, including every custom date. Stops are ordered chronologically. If a milestone date is the same as an annual stop or another milestone date, show it in that stop's accessible label rather than adding a duplicate position.
- **FR-14-02 — Dynamic stops:** Rebuild slider ticks and labels when a standard or custom milestone date is added, changed, overridden, reset, or deleted. Preserve the selected date when it remains available; otherwise select the nearest remaining timeline stop and announce the change.
- **FR-14-03 — Navigation:** The range slider, keyboard operation, and previous/next buttons navigate the same ordered timeline stops. Expose the exact selected year or milestone label/date through the slider's accessible value text and adjacent output.
- **FR-14-04 — Range boundaries:** Keep the annual Year 1 and Year 6 endpoints identifiable. Dated milestones outside the annual data range remain selectable and visible on the chart.

## 2. Interpolated Snapshots

- **FR-14-05 — Date-based interpolation:** At a selected milestone date between annual sample dates, linearly interpolate each asset/debt category for each party using elapsed UTC calendar days between the surrounding annual sample dates. Round to the nearest whole dollar. Derive Combined and Net assets from the resulting party values.
- **FR-14-06 — No extrapolation:** At dates before the first or after the last annual sample date, do not extrapolate. Use the nearest endpoint sample and explicitly say that no annual data exists beyond that endpoint.
- **FR-14-07 — Honest prominent notice:** When showing an interpolated snapshot, display a prominent red/amber notice that calls the values fictional interpolations, identifies the selected milestone and exact date, explains that values are not source facts, and says users can edit the estimate. The notice is programmatically exposed to assistive technology.
- **FR-14-08 — Annual snapshots:** Selecting an annual stop continues to show its original annual sample unless that annual sample was edited in the current page session.
- **FR-14-09 — Editing interpolated dates:** The existing edit mode works at an interpolated milestone date. Saving creates or updates a session-only snapshot override for that exact date, without changing annual samples. The chart includes that point and redraws its series through it. Clearly identify the override as a fictional, user-edited, page-only value. Cancel discards pending edits.
- **FR-14-10 — Milestone edits:** Editing, resetting, or deleting a milestone updates the slider stops and selected date safely. Removing a selected milestone clears its chart highlight without losing the nearest valid slider position.

## 3. Chart, Accessibility, and Boundaries

- **FR-14-11 — Chart synchronization:** The chart cursor follows the exact selected stop and reflects its comparison total. Include all dated milestone markers, including those outside the original annual range. Plot annual values, milestone-date samples, and saved interpolated-date overrides in chronological order while preserving all annual points.
- **FR-14-12 — Semantic controls:** Keep the year/date range labeled; provide accessible tick labels and selected-value text. Previous/next controls remain named for timeline points and disabled at the first/last stop.
- **FR-14-13 — Responsive layout:** Keep slider, endpoint labels, date notices, and controls usable on narrow screens without page-level horizontal overflow.
- **FR-14-14 — Local-only demo:** Milestone stops and interpolated/edited values exist only in page memory. Do not send values to an API/provider or write to browser storage. Reload restores the original sample values and standard demo dates.

## 4. Acceptance Criteria

1. All six annual dates remain reachable, and each available custom date appears at its exact chronological slider stop.
2. Adding, editing, resetting, and deleting custom dates immediately updates slider ticks, accessible labels, navigation, and chart markers.
3. Selecting an in-range custom date displays date-based interpolated category and party values, with calculated Combined and Net assets.
4. The interpolated notice is visibly red/amber highlighted and clearly says the values are fictional/interpolated and can be edited.
5. Out-of-range dates are selectable, use the nearest endpoint values, and explicitly state that no extrapolation occurred.
6. Editing an interpolated date changes only the session-only point at that exact date and redraws the chart through it; cancel discards changes.
7. Annual stops, keyboard controls, responsive layout, and local-only demo boundaries remain intact.
