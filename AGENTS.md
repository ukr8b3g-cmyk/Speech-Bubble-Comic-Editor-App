# Repository instructions

Scope: entire repository.

- This repository is the standalone successor to `Speech-Bubble-4koma-Editor`.
- Phase 1 baseline is upstream commit `af7f79d896823f39f19fa936602317e39164a827` (v0.1.8 series).
- Forge feature source is `Speech-Bubble-Comic-Editor-for-Forge-Neo`; port editing behavior, not Forge host adapters.
- Preserve the standalone Windows/pywebview architecture, `.sbeproj` compatibility, and the three existing workspaces.
- Keep the predecessor repository unchanged. Do not replace Desktop APIs with Forge routes/settings/launchers.
- Before changes, inspect `git status` and preserve unrelated or uncommitted work.
- Prefer focused phase commits. Run Python compile checks, JavaScript syntax checks, and relevant targeted tests after changes.
