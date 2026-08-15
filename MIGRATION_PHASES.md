# Speech Bubble Comic Editor App migration phases

## Phase 1 — Standalone successor baseline

- Import the Speech Bubble 4koma Editor v0.1.8-series baseline at `af7f79d896823f39f19fa936602317e39164a827`.
- Rename the standalone product, executable/build files, icon path, installer identity, Windows product metadata, mutex/event identity, and local application-data root to Speech Bubble Comic Editor App.
- Preserve `.sbeproj`, project schema, three workspace modes, save/recovery/export behavior, and existing editing behavior.
- Do not import Forge-specific adapters or settings integration.

## Phase 2 — Shared Page Images and shared core fixes

- Port the Forge 0.7.10 Page Images behavior to the standalone app: the tray is visible in Single Image, 4-Panel Manga, and Comic and defaults to shared across all three workspaces.
- Add the standalone `shared_project_images` setting and keep the Forge-equivalent default enabled while preserving Desktop settings/storage APIs.
- Persist Page Images tray state in `.sbeproj`, include tray-only images in project saves, and keep shared-image removal, Undo/Redo, workspace switching, and legacy project loading consistent.
- Single Image replacement now follows the Forge 0.7.9 behavior: direct replacement refits the image, automatically follows image dimensions on an otherwise empty page, and asks before resizing an edited page. New +Image layers remain additive and start unlocked.
- The verified 4-Panel Page Images placement fix is included. Duplicate tray insertion when reusing an existing Page Image remains a separate follow-up.

## Phase 3 — Crop and alignment

- Port non-destructive image crop across Single Image, 4-Panel Manga, and Comic. Single Image supports inline crop editing; panel images use the reusable crop dialog.
- Preserve crop state in each image/panel object and reset it only when a new source image is assigned or the user explicitly resets/fits it.
- Port panel-image rotation and use the shared cropped/rotated image draw path so crop, rotation, flip, opacity, Cover/Contain, scale, and offset remain consistent.
- Port multi-selection align/distribute controls with Selection Objects, common Panel, and Page references. Alignment requires 2+ editable objects and distribution requires 3+.
- Port grouped relative rotation while preserving each selected object's relative center and starting rotation.
- Phase 3 implementation complete; Quick Retouch remains Phase 4.

## Phase 4 — Quick Retouch

- Port Forge Neo 0.7.10 Quick Retouch without Forge host adapters or server dependencies.
- Single Image applies the result as a new image layer while preserving the source layer.
- 4-Panel Manga and Comic add the result back to Page Images through the existing editor image pipeline.
- Keep `.sbeproj` and Project Schema unchanged; Quick Retouch document/history state remains transient.
- Phase 4 implementation complete; Phase 5 processing-diff integration is next.

## Phase 5 — Processing diff integration

Merge only the later Forge-side Background Removal and Comic Conversion improvements that are not already present in the standalone app.

## Phase 6 — Regression, packaging, and release preparation

Run full regression/build validation, reconcile documentation and packaging, and prepare the first successor-app release.


## Phase 5 — Forge 0.7.10 parity and processing fixes

Phase 5 completed: processing source identity, batch image rendering, multi-text editing, per-drawer state, Desktop Supersample, bilingual UI/tooltips, and Page Images ID-reuse regression coverage.
