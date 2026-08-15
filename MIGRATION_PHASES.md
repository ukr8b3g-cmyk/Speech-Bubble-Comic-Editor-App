# Speech Bubble Comic Editor App migration phases

## Phase 1 — Standalone successor baseline

- Import the Speech Bubble 4koma Editor v0.1.8-series baseline at `af7f79d896823f39f19fa936602317e39164a827`.
- Rename the standalone product, executable/build files, icon path, installer identity, Windows product metadata, mutex/event identity, and local application-data root to Speech Bubble Comic Editor App.
- Preserve `.sbeproj`, project schema, three workspace modes, save/recovery/export behavior, and existing editing behavior.
- Do not import Forge-specific adapters or settings integration.

## Phase 2 — Shared core fixes

Port later Forge-side editor bug fixes that are applicable to the standalone app, including image replacement, history/state, and Comic/4-panel core fixes.

## Phase 3 — Crop and alignment

Port non-destructive image crop across Single Image, 4-Panel Manga, and Comic plus multi-selection alignment/distribution.

## Phase 4 — Quick Retouch

Port Quick Retouch and adapt its image input/output, settings, persistence, and application routes to the Desktop APIs.

## Phase 5 — Processing diff integration

Merge only the later Forge-side Background Removal and Comic Conversion improvements that are not already present in the standalone app.

## Phase 6 — Regression, packaging, and release preparation

Run full regression/build validation, reconcile documentation and packaging, and prepare the first successor-app release.
