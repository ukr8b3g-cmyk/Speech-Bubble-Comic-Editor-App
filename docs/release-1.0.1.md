# Speech Bubble Comic Editor App v1.0.1 — Windows x64

Bug-fix release for project data safety and portable assets. The standalone Windows / pywebview architecture, three workspaces and `.sbeproj` archive format version 1 are maintained. Previous v1.0 and v0.1.8 releases remain available with their original assets.

## Changes

- **Project data protection:** Save Layout / Ctrl+S no longer marks an unsaved `.sbeproj` as committed. Project save tracks the exact snapshot sent to disk; changes occurring during saving remain unsaved.
- **Open / New / Exit:** project replacement has Save / Discard / Cancel confirmation. Concurrent changes during loading abort replacement.
- **External palette:** incoming edits are included in the main window's undo/dirty/autosave update flow.
- **Portable custom stamps:** used user-defined stamp images are bundled into newly saved projects and resolved by asset ID at load time. Legacy projects without bundled stamps remain readable but require their user assets to be available.
- **Overlay PNG:** Desktop save_overlay setting is passed to the renderer and used by server exports for PNG, JPEG and WebP.
- **Recovery discard:** explicit discard suppresses an old recovery generation from returning at startup.

## Downloads

- **Installer**: [SpeechBubbleComicEditorApp-v1.0.1-win-x64-setup.exe](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/releases/download/v1.0.1/SpeechBubbleComicEditorApp-v1.0.1-win-x64-setup.exe)
- **Portable ZIP**: [SpeechBubbleComicEditorApp-v1.0.1-win-x64-portable.zip](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/releases/download/v1.0.1/SpeechBubbleComicEditorApp-v1.0.1-win-x64-portable.zip)
- **SHA-256**: [SHA256SUMS.txt](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/releases/download/v1.0.1/SHA256SUMS.txt)

Use the installer for normal use, or extract the ZIP and launch `SpeechBubbleComicEditorApp.exe`. Existing releases are preserved: [v1.0](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/releases/tag/v1.0) and [v0.1.8](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/releases/tag/v0.1.8).

## Verification and remaining limits

The Windows GitHub Actions workflow runs Python and JavaScript regression suites, packages Installer/Portable ZIP from the same build, verifies Windows installer output and checks SHA-256 manifests before release publication. New regression tests exercise project stamp blobs, Overlay output in all three formats and the recovery discard marker.

No new clean-Windows installation/upgrade/uninstallation, native file-picker, end-to-end WebView2 editing session or ONNX real-inference gate is asserted for v1.0.1. Fonts are referenced by identity and are not embedded; retain backups of important projects when upgrading.
