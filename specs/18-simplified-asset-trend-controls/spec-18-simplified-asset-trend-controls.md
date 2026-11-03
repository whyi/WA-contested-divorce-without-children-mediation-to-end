# Spec 18: Simplified Asset-Trend Milestone Controls

- **Status:** Implemented
- **Related issue:** [#68 — Simplify milestone selection in the illustrative asset trend](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/68)
- **Related specifications:** [Spec 10: Mock Asset-Analysis Dashboard](../10-mock-asset-analysis-dashboard/spec-10-mock-asset-analysis-dashboard.md), [Spec 11: Relationship Milestone Timeline](../11-relationship-milestone-timeline/spec-11-relationship-milestone-timeline.md), and [Spec 14: Custom Dates on the Timeline Slider](../14-custom-dates-on-timeline-slider/spec-14-custom-dates-on-timeline-slider.md)
- **Objective:** Simplify the illustrative asset-trend chart by removing its redundant milestone highlight list and using the selector above the chart as the single milestone-selection control.
- **Scope:** The local-only sample asset trend's milestone selector, chart markers, and duplicate list of milestone highlight actions. Milestone management, dates, asset values, chart series, and timeline-slider behavior remain unchanged.

## 1. Milestone Selection

- **FR-18-01 — Single selector:** Keep one labeled milestone selector above the chart as the primary control for selecting or clearing a milestone highlight.
- **FR-18-02 — Remove duplicate list:** Do not render a second list of available milestones or per-milestone **Highlight** buttons below the chart.
- **FR-18-03 — Selection synchronization:** Selecting or clearing a value in the selector updates the chart highlight and accessible selection status. Existing pointer and keyboard activation of a chart marker remains available and synchronizes the selector.
- **FR-18-04 — Preserve timeline semantics:** Keep existing behavior for the selected timeline stop and comparison snapshot. Changing milestone selection must not modify sample values or change how the timeline slider works.
- **FR-18-05 — Preserve milestone details:** Continue to show available dates and provenance in the selector, and retain the separate milestone-management controls for editing standard and custom dates.

## 2. Boundaries and Accessibility

- **FR-18-06 — Local-only demo:** Milestone selection remains page-only. Do not send or save the selection or sample values.
- **FR-18-07 — Accessible status:** Keep the selector labeled, keep chart markers keyboard operable, and announce the selected or cleared milestone through the existing status region.
- **FR-18-08 — Responsive layout:** Present the selector in a clear, compact layout above the chart without introducing page-level horizontal overflow.

## 3. Acceptance Criteria

1. The asset trend has one milestone selector above the chart and no duplicate milestone highlight list below it.
2. The selector still presents available milestone labels, dates, and provenance and supports clearing the selection.
3. Selecting or clearing a milestone synchronizes the selector, chart highlight, and accessible status.
4. Chart markers remain pointer- and keyboard-operable and synchronize their selection with the selector.
5. Milestone management, timeline stops, selected snapshot behavior, sample values, and local-only boundaries remain unchanged.
