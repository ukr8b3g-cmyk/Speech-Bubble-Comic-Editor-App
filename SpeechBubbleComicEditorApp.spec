from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


root = Path(SPECPATH)

a = Analysis(
    [str(root / "desktop_launcher.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "web"), "web"),
        (str(root / "README.md"), "."),
        (str(root / "LICENSE"), "."),
        (str(root / "PRIVACY.md"), "."),
        (str(root / "SECURITY.md"), "."),
        (str(root / "THIRD-PARTY-NOTICES.md"), "."),
    ],
    hiddenimports=[
        *collect_submodules("uvicorn"),
        *collect_submodules("webview"),
        *collect_submodules("onnxruntime"),
        "webview.platforms.edgechromium",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SpeechBubbleComicEditorApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(root / "web" / "assets" / "speech-bubble-comic-editor-app.ico"),
    version=str(root / "packaging" / "windows_version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="SpeechBubbleComicEditorApp",
)
