from pathlib import Path
import json
from desktop_app.settings_store import SettingsStore

def test_supersample_roundtrip(tmp_path: Path):
    store=SettingsStore(tmp_path / "settings.json")
    assert store.load()["supersample"] == 2
    assert store.save({"supersample": 4})["supersample"] == 4
    assert store.save({"supersample": 99})["supersample"] == 4
    assert store.save({"supersample": 0})["supersample"] == 1

def test_public_settings_reads_desktop_supersample(tmp_path: Path, monkeypatch):
    (tmp_path / "settings.json").write_text(json.dumps({"supersample": 4}), encoding="utf-8")
    monkeypatch.setenv("SPEECH_BUBBLE_DESKTOP_DATA_ROOT", str(tmp_path))
    from speech_bubble_editor.settings import public_settings
    assert public_settings().supersample == 4
