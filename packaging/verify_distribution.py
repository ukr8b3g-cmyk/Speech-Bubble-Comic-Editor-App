"""Verify the generated Windows ZIP, bundled editor assets, and licenses."""
from pathlib import Path
import json
import runpy
import subprocess
import sys
import tempfile
import zipfile

root = Path(__file__).resolve().parents[1]
archive = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='sbe-release-check-') as temp:
    destination = Path(temp)
    with zipfile.ZipFile(archive) as package:
        package.extractall(destination)
    app = destination / 'SpeechBubbleComicEditorApp'
    internal = app / '_internal'
    for name in ['licenses/MangaScreen-MIT.txt', 'THIRD-PARTY-NOTICES.md',
                 'README.md', 'web/speech-bubble-editor.html', 'web/desktop/vendor/ag-psd.js',
                 *(path.relative_to(root) for path in (root / 'licenses').glob('ag-psd-*.txt'))]:
        assert (internal / name).read_bytes() == (root / name).read_bytes(), name
    assert (app / 'THIRD-PARTY-NOTICES.md').read_bytes() == (root / 'THIRD-PARTY-NOTICES.md').read_bytes()
    display_version = runpy.run_path(str(root / 'desktop_app/version.py'))['APP_DISPLAY_VERSION']
    html = (internal / 'web/speech-bubble-editor.html').read_text(encoding='utf-8')
    app_title = f'Speech Bubble Comic Editor App {display_version}'
    assert f'<title>{app_title}</title>' in html, 'Page title version mismatch'
    assert f'<strong>{app_title}</strong>' in html, 'Header version mismatch'
    license_text = (internal / 'licenses/MangaScreen-MIT.txt').read_text(encoding='utf-8')
    for phrase in ['Copyright (c) 2026 ashukae', 'Permission is hereby granted',
                   'THE SOFTWARE IS PROVIDED "AS IS"']:
        assert phrase in license_text
    metadata = list(internal.glob('opencv_python_headless-*.dist-info'))
    assert any(list(directory.rglob('LICENSE*')) for directory in metadata), 'OpenCV license missing'
    report = destination / 'self-test.json'
    subprocess.run([str(app / 'SpeechBubbleComicEditorApp.exe'),
                    '--manga-finish-self-test', str(report)], check=True, timeout=90)
    result = json.loads(report.read_text(encoding='utf-8'))
    assert result['ok'], result
    print(json.dumps({'zip_assets_match_source': True, 'display_version': display_version,
                      'mangascreen_mit_included': True,
                      'opencv_license_included': True, 'exe_self_test': result}))
