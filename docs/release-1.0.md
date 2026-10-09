# Speech Bubble Comic Editor App 1.0

Windows x64 standalone release. Application and installer display version: **1.0**. Project/package version: **1.0.0**.

## Changes

- Localized all 190 built-in SFX and 94 stamps by stable asset ID. Cards, layers, tooltips, accessible names and favorites now use the same name in the selected language.
- Japanese SFX artwork is preserved. English names use the written pronunciation; descriptions are added only for clear meanings. Ambiguous sounds retain their pronunciation.
- Search retains Japanese names, English names, aliases and keywords. Name sorting follows the UI language. Dynamic catalogs preserve their supplied English names.
- Localized save, draft, export, font-loading and failure messages, unsaved-change prompts, text properties and image-tool hints.
- Kept user dialogue, user asset names, serialized IDs and the existing `.sbeproj` format.
- Aligned application, package, Windows version resources, setup filenames, README and CI with 1.0.

## Validation

- Python compile checks and 23 Python regression tests.
- JavaScript syntax checks and 24 JavaScript regression scripts, including coverage of all 286 bundled IDs (two hidden), dynamic catalog names and preservation of user names.
- Real local Desktop API with an Edge browser: 190 SFX / 94 stamps, Japanese and English search, English Name sorting, repeated JA/EN switching, existing layer labels, SFX and text editing, `.sbeproj` save/reopen and PNG export.
- English text/attribute audit of the editor, text properties, font browser, Settings, unsaved changes, Quick Retouch, Background Removal and Comic Conversion.

## Files

- `SpeechBubbleComicEditorApp-v1.0-win-x64-setup.exe`
- `SpeechBubbleComicEditorApp-v1.0-win-x64-portable.zip`
- `SHA256SUMS.txt`

Use the installer for normal use. The portable ZIP contains the same application build. Previous releases remain available.
