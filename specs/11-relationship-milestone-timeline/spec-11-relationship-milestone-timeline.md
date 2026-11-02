# Spec 11: Relationship Milestone Timeline

- **Status:** Draft
- **Related issue:** [#51 — Highlight key relationship milestones on the asset timeline](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/issues/51)
- **Related specification:** [Spec 10: Mock Asset-Analysis Dashboard](../10-mock-asset-analysis-dashboard/spec-10-mock-asset-analysis-dashboard.md)
- **Objective:** Let users see and manage important relationship and divorce-related dates alongside the fictional asset timeline, without implying that missing dates are known or that the demo extracted real case facts.
- **Scope:** Standard relationship milestone dates, user overrides, custom labeled dates, milestone selection, and chart markers in the existing local-only analysis preview. Date extraction, verification, legal interpretation, and backend persistence are outside this specification.

## 1. Milestone Data and Provenance

- **FR-11-01 — Standard milestone list:** Provide standard milestones for start of cohabitation / committed intimate relationship (CIR), marriage, separation, and divorce petition filing.
- **FR-11-02 — Missing dates:** A standard milestone without a date remains visible in the selector as **N/A** and cannot be selected. Never infer or fabricate a missing standard date.
- **FR-11-03 — Available dates:** A standard milestone becomes available when supplied with a valid date from an upstream source or entered by the user. Accept analyzed dates through the `casework:milestones-extracted` browser event, whose detail maps standard milestone IDs to ISO `YYYY-MM-DD` dates (or `null` when not found). This spec does not implement document parsing.
- **FR-11-04 — Date provenance:** Distinguish an upstream/extracted date from a user-entered or overridden date. Do not present an unverified extracted date as confirmed.
- **FR-11-05 — Override:** In the milestone manager, let the user set or replace the date of any standard milestone using its date/calendar control. Preserve the entered date as the active value and identify that it was user-overridden in the UI. Let the user reset the override to the latest upstream date.
- **FR-11-06 — Date validity:** Accept valid calendar dates only. Reject invalid or incomplete values with an accessible inline explanation and do not render them as timeline markers.

## 2. Custom Milestones

- **FR-11-07 — Collapsible manager:** Place a clearly labeled **Manage milestone dates** section near the top of the analysis view. It starts collapsed and can be expanded or collapsed without losing in-page state. Put all standard milestone fields and the custom-date manager inside this same section.
- **FR-11-07a — Standard milestone fields:** Show cohabitation/CIR start, marriage, separation, and petition filing as individual rows in the manager. Display an upstream analyzed date in its row with unverified provenance; show **N/A** when no date is available. Each row supports user override and reset.
- **FR-11-08 — Create custom date:** Within the same milestone manager, allow users to add any number of custom milestones, each with a user-defined non-empty label and a valid date.
- **FR-11-09 — Edit and delete:** Allow users to change a custom milestone's label or date and to delete it. Confirm destructive deletion accessibly before removing a custom item.
- **FR-11-10 — Custom date validation:** Prevent empty labels, invalid dates, and duplicate custom labels after trimming surrounding whitespace. Explain validation errors next to the relevant field.
- **FR-11-11 — Local-only changes:** Standard-date overrides, custom dates, and selection state exist only in the current page session. Do not send them to an API, database, or browser storage.

## 3. Selector and Timeline Chart

- **FR-11-12 — Milestone selector:** Provide a selector above the chart containing all standard milestones and all custom milestones. Show each item's label/type and its date when available; show **N/A** and disable standard items with no date.
- **FR-11-13 — Selection behavior:** Selecting an available milestone highlights and identifies its corresponding chart marker. Keep all asset series and the complete asset timeline visible. Clearing or changing the selection removes or moves the highlight without changing asset values or the selected annual snapshot.
- **FR-11-14 — Chart markers:** Render every available milestone at its date on the timeline using a visual treatment distinct from annual asset-series points. Markers must remain distinguishable without color alone and expose the milestone label and date to assistive technology.
- **FR-11-15 — Date range:** Never silently clamp, omit, or misplace a milestone whose date falls outside the chart's plotted interval. Extend the displayed timeline to include it or show an explicit, accessible out-of-range indication linked to the milestone.
- **FR-11-16 — Overlapping dates:** If multiple milestones share or nearly share a date, keep each item selectable and individually identifiable; prevent one marker or label from obscuring the others.
- **FR-11-17 — Dynamic updates:** Adding, editing, overriding, or deleting a date updates the selector and chart markers immediately. Removing a selected custom milestone clears the selection safely.
- **FR-11-18 — Fictional demo labeling:** Any dates supplied by the demo are explicitly labeled fictional. The UI must not suggest that dates were parsed from uploaded documents or belong to a real case.

## 4. Accessibility and Responsive Behavior

- **FR-11-19 — Keyboard and screen readers:** The collapsible section, form controls, selector, validation feedback, and chart markers are operable and understandable with keyboard and assistive technology. Announce milestone changes and the currently selected milestone through an appropriate live status.
- **FR-11-20 — Narrow screens:** Keep date-management controls and the selector usable on narrow screens. The chart may scroll horizontally, but milestone labels and selected-marker information remain discoverable.

## 5. Acceptance Criteria

1. All four standard milestone types appear in the selector; missing dates display as disabled **N/A** options.
2. The top-level **Manage milestone dates** section contains all four standard milestone rows and the custom-date manager.
3. An analyzed standard date is populated in its matching row with unverified provenance; an unavailable date displays as N/A. A valid user override replaces the active date and can be reset to the upstream value.
4. Users can create, edit, and delete multiple custom labeled dates in that same collapsible section; invalid values are rejected with accessible field-level feedback.
5. Available standard and custom dates appear at their corresponding positions on the timeline and can be selected to highlight an individually identifiable marker.
6. Milestone selection leaves the complete asset timeline, asset series, and selected annual asset snapshot intact.
7. Dates outside the plotted interval and overlapping dates remain explicitly represented and accessible.
8. All changes are local-only; the demo does not call an AI provider or save or transmit milestone values.
9. Demo dates are clearly fictional and no missing or unverified case date is presented as fact.
10. Keyboard, screen-reader, and narrow-screen users can manage dates, use the selector, and identify chart markers.
