"""Regression coverage for portable stamp blobs and Overlay output settings."""
import base64
import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from PIL import Image

from desktop_app.paths import DesktopPaths
from desktop_app.project_store import ProjectStore
from desktop_app.server import create_app
from desktop_app.settings_store import SettingsStore


def paths_for(root):
    paths = DesktopPaths(root=root, settings=root / "settings.json", recent=root / "recent.json",
                         recovery=root / "recovery", cache=root / "cache", logs=root / "logs",
                         temp=root / "temp", models=root / "models")
    for directory in (root, paths.recovery, paths.cache, paths.logs, paths.temp, paths.models):
        directory.mkdir(parents=True, exist_ok=True)
    return paths


def png():
    out = io.BytesIO()
    Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(out, "PNG")
    return out.getvalue()


def layout(asset_id):
    item = {"id": "stamp", "type": "sfx", "user_asset_id": asset_id,
            "asset_src": "http://127.0.0.1:8069/old-asset"}
    sizes = {"single": (1024, 1024), "comic": (720, 2200), "comic_layout": (2480, 3508)}
    return {"format": "speech-bubble-editor-layout", "version": 5, "active_workspace": "single",
            "workspaces": {name: {"canvas": {"width": w, "height": h},
                                 "elements": [item] if name == "single" else []}
                           for name, (w, h) in sizes.items()}}


class StampOverlayTest(unittest.TestCase):
    def test_embedded_stamp_and_legacy_roundtrip(self):
        raw = png()
        stamp_id = hashlib.sha256(raw).hexdigest()
        record = {"id": "user-asset:" + stamp_id, "name": "stamp",
                  "mime": "image/png", "data_url": "data:image/png;base64," +
                  base64.b64encode(raw).decode("ascii")}
        with tempfile.TemporaryDirectory() as folder:
            store = ProjectStore()
            path = Path(folder) / "saved.sbeproj"
            store.save(path, {"layout": layout(stamp_id), "images": [record]})
            loaded = store.load(path)
            self.assertEqual(loaded["images"][0]["data_url"], record["data_url"])
            legacy = Path(folder) / "legacy.sbeproj"
            store.save(legacy, {"layout": layout(stamp_id), "images": []})
            self.assertEqual(store.load(legacy)["images"], [])

    def test_overlay_all_formats(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = paths_for(root / "app")
            client = TestClient(create_app(paths, "token"))
            headers = {"X-SBE-Token": "token"}
            settings = SettingsStore(paths.settings)
            settings.save({"save_overlay": True})
            redirect = client.get("/", follow_redirects=False)
            self.assertEqual(parse_qs(urlparse(redirect.headers["location"]).query)["saveOverlay"], ["1"])
            data_url = "data:image/png;base64," + base64.b64encode(png()).decode("ascii")
            output = root / "output"
            output.mkdir()
            for fmt in ("png", "jpeg", "webp"):
                settings.save({"output_format": fmt, "save_overlay": True})
                response = client.post("/speech-bubble-editor/export", headers=headers, json={
                    "render_mode": "browser_canvas_v1", "composite_data_url": data_url,
                    "overlay_data_url": data_url, "layout_json": "{}", "name": "stamp",
                    "desktop_output_dir": str(output),
                })
                self.assertEqual(response.status_code, 200, response.text)
                saved = response.json()
                self.assertTrue(saved["save_overlay"])
                self.assertTrue((Path(saved["output_dir"]) / saved["filename"]).is_file())
                overlay = Path(saved["output_dir"]) / saved["overlay_filename"]
                with Image.open(overlay) as opened:
                    self.assertEqual(opened.format, "PNG")
