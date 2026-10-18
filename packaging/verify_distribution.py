"""Verify the generated Windows ZIP, including the MangaScreen MIT license."""
from pathlib import Path
import json
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
                 'README.md', 'web/speech-bubble-editor.html']:
        assert (internal / name).read_bytes() == (root / name).read_bytes(), name
    assert (app / 'THIRD-PARTY-NOTICES.md').read_bytes() == (root / 'THIRD-PARTY-NOTICES.md').read_bytes()
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
    print(json.dumps({'zip_assets_match_source': True, 'mangascreen_mit_included': True,
                      'opencv_license_included': True, 'exe_self_test': result}))
