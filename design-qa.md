# Design QA

## Background removal

- Reference: `docs/qa/reference-background-removal.png`
- Implementation: `docs/qa/background-removal-v0.1.3.png`
- Combined comparison: `docs/qa/background-removal-comparison.png`
- Test viewport: 1404 × 1154
- Test source: 896 × 1152 WebP shown in the reference
- Runtime state: maximized dialog, isnet-anime CPU inference complete, transparent-result mode

Visual comparison confirmed the same primary structure: compact title/header, source metadata, source and result canvases, right-side editing tools, bottom status and confirmation actions. Borders, spacing, dark theme, canvas fitting, and sticky footer remain readable without clipping at the reference viewport.

Intentional differences:

- The implementation is an in-app movable/resizable dialog, so it does not reproduce the native Windows minimize control shown in the concept image.
- `Transparent Result` shows the final alpha result. The red deletion overlay is available as the separate `Red Mask Overlay` display mode defined by the implementation specification.
- Model state and advanced mask controls remain in the scrollable right panel instead of reducing the preview area.

Result: passed.

## Heading Properties and page-image tray

- Implementation: `docs/qa/heading-properties-v0.1.3.png`
- Test viewport: 1404 × 1154

Verified in the running app:

- Heading Properties shows `見出し　☑ 見出しを表示` in one top row.
- The duplicate right-side type label is hidden only for the heading target.
- The lower duplicate checkbox and inert `＋ 見出しBoxを追加` control are absent.
- The move/resize hint remains below the geometry fields.
- Toggling the title checkbox changes the Layers eye between `◉` and `○` and restores it correctly.
- The page-image heading toggles `aria-expanded` from `false` to `true`; the add-image button remains a separate control.
- English mode shows `Header Box` and `Show Header`.

Result: passed.
