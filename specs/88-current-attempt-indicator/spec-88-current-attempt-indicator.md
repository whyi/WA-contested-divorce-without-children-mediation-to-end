# Spec 88: Noninteractive current-attempt indicator

This specification amends spec 80's attempt navigation behavior. Prior specs
remain unchanged.

- On the current attempt's Asset Overview, its circle is an indicator, not an
  action. Disable its button, use the default cursor, and prevent navigation,
  including synthetic click dispatch. Apply this to real cases and both demos.
- Future positions and unavailable archive snapshots stay disabled.
- Available archived attempts remain selectable for read-only review. While
  viewing an archive, enable the current-attempt button to return to the working
  attempt; disable it again upon returning. Do not strand users in an archive.
- Keep circle styling, current labels, attempt limits, and saved data unchanged.
- Verify the Free single circle, paid current circle, demo parity, and archive
  review followed by return to current.
