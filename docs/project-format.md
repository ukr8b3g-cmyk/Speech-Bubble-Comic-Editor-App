# Project format

`.sbeproj` is a ZIP archive containing the following files:

```text
manifest.json
layout.json
comic.json
images/<sha256>.<extension>
```

`layout.json` is the canonical document layout.  `comic.json` mirrors the
optional comic state so older project readers can retain their existing
sidecar-file workflow.  Image blobs are content-addressed by SHA-256; the
manifest keeps the logical image IDs that are referenced from the layout.

## Current versions

| Value | Current version | Meaning |
| --- | --- | --- |
| Project archive / manifest | 1 | ZIP file layout |
| Layout schema | 4 | Single-image and comic workspaces |
| Comic state | 1 | Current vertical four-panel state |
| Recovery record | 1 | Autosave record format |
| Application | 0.1.6 | Application release recorded in new manifests |

The archive version changes only when the ZIP file layout changes.  A layout
or comic data-model change uses its respective schema version instead.
Application version is informational and is not used for schema compatibility.

## Compatibility and migrations

- Old layouts without a version remain readable through the existing legacy
  migration path.
- A newer layout, comic, archive, or recovery version is rejected rather than
  being silently opened as an empty project.
- Future generic-comic work should first raise `comic.version` and supply an
  explicit migration (for example, vertical four-panel v1 to a page model v2).
- Do not raise the archive version unless the ZIP structure itself changes.
- Keep legacy-project loading tests when changing the format.

## Persistence boundary

The project layout stores the work itself: workspaces, canvas settings,
layers, image references, and comic state.  Transient UI state should remain
separate where possible, so a future editor can change its interface without
changing the document format.
