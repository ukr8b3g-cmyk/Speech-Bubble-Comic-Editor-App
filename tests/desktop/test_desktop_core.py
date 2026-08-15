from __future__ import annotations

import base64
import hashlib
import io
import json
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from unittest import mock

from fastapi.testclient import TestClient
from PIL import Image

from desktop_app.paths import DesktopPaths
from desktop_app.main import DesktopBridge, normalized_window_geometry
from desktop_app.project_store import ProjectStore
from desktop_app.recent_projects import RecentProjects
from desktop_app.recovery_store import RecoveryStore
from desktop_app.server import create_app
from desktop_app.settings_store import SettingsStore
from speech_bubble_editor.font_catalog import _font_cmap_is_browser_safe, _font_display_names
from speech_bubble_editor.renderer import get_sfx_asset_catalog


def make_paths(root: Path) -> DesktopPaths:
    paths = DesktopPaths(
        root=root,
        settings=root / "settings.json",
        recent=root / "recent.json",
        recovery=root / "recovery",
        cache=root / "cache",
        logs=root / "logs",
        temp=root / "temp",
        models=root / "models",
    )
    for directory in (paths.root, paths.recovery, paths.cache, paths.logs, paths.temp, paths.models):
        directory.mkdir(parents=True, exist_ok=True)
    return paths


def png_data_url() -> str:
    output = io.BytesIO()
    Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(output, format="PNG")
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def current_layout(
    *,
    active_workspace: str = "single",
    single_elements: list[dict] | None = None,
    comic_elements: list[dict] | None = None,
    general_elements: list[dict] | None = None,
    comic: dict | None = None,
    general_comic: dict | None = None,
) -> dict:
    single = {
        "canvas": {"width": 1024, "height": 1024},
        "background_visible": True,
        "canvas_background": {"color": "#ffffff", "transparent": False},
        "elements": list(single_elements or []),
    }
    comic_workspace = {
        "canvas": {"width": 720, "height": 1600},
        "background_visible": True,
        "elements": list(comic_elements or []),
    }
    general_workspace = {
        "canvas": {"width": 2480, "height": 3508},
        "background_visible": True,
        "elements": list(general_elements or []),
    }
    workspaces = {
        "single": single,
        "comic": comic_workspace,
        "comic_layout": general_workspace,
    }
    active = workspaces[active_workspace]
    result = {
        "format": "speech-bubble-editor-layout",
        "version": 5,
        "active_workspace": active_workspace,
        "canvas": dict(active["canvas"]),
        "background_visible": active["background_visible"],
        "elements": list(active["elements"]),
        "workspaces": workspaces,
    }
    if comic is not None:
        result["comic"] = comic
    if general_comic is not None:
        result["general_comic"] = general_comic
    return result


class DesktopCoreTest(unittest.TestCase):
    def test_dynamic_sfx_catalog_keeps_manifest_geometry(self) -> None:
        get_sfx_asset_catalog.cache_clear()
        items = {item["id"]: item for item in get_sfx_asset_catalog()["items"]}
        self.assertEqual((items["jupu-mask"]["w"], items["jupu-mask"]["h"]), (406, 614))
        self.assertEqual(
            (items["sfx-builtin-papu-small-tsu"]["sortGroup"], items["sfx-builtin-papu-small-tsu"]["sortRank"]),
            (50, 4),
        )
        self.assertEqual(
            (
                items["sfx-builtin-papu-small-tsu"]["fill"],
                items["sfx-builtin-papu-small-tsu"]["stroke"],
                items["sfx-builtin-papu-small-tsu"]["outlineWidth"],
            ),
            ("#EC407A", "#111111", 3),
        )

    def test_desktop_bridge_keeps_native_objects_private(self) -> None:
        bridge = DesktopBridge()
        self.assertNotIn("window", bridge.__dict__)
        self.assertNotIn("palette_window", bridge.__dict__)
        self.assertNotIn("webview", bridge.__dict__)
        self.assertIn("_window", bridge.__dict__)
        self.assertIn("_palette_window", bridge.__dict__)
        self.assertIn("_webview", bridge.__dict__)

    def test_recovery_round_trip_generations_and_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RecoveryStore(Path(temporary) / "recovery")
            for index in range(7):
                result = store.save(
                    {
                        "title": "autosave",
                        "project_path": "C:/Projects/sample.sbeproj",
                        "layout": {"canvas": {"width": 720, "height": 2160}, "revision": index},
                        "images": [
                            {
                                "id": "image-1",
                                "name": "panel.png",
                                "mime": "image/png",
                                "data_url": png_data_url(),
                            }
                        ],
                    },
                    checkpoint=True,
                )
                self.assertTrue(result["ok"])
            status = store.status()
            self.assertEqual(status["generations"], 5)
            self.assertEqual(status["assets"], 1)
            self.assertEqual(store.load()["layout"]["revision"], 6)

            store.current.write_text("{broken", encoding="utf-8")
            self.assertTrue(store.status()["available"])
            fallback = store.load()
            self.assertEqual(fallback["fallback_generation"], 1)
            self.assertEqual(fallback["layout"]["revision"], 6)
            self.assertEqual(fallback["manifest"]["project_path"], "C:/Projects/sample.sbeproj")
            self.assertGreater(store.clear(), 0)
            self.assertFalse(store.status()["available"])

    def test_window_geometry_is_clamped_to_available_work_area(self) -> None:
        with mock.patch(
            "desktop_app.main._work_areas",
            return_value=[(0, 0, 1920, 1080)],
        ):
            geometry = normalized_window_geometry(
                {
                    "window_width": 5000,
                    "window_height": 5000,
                    "window_left": 5000,
                    "window_top": 5000,
                    "window_maximized": False,
                }
            )
        self.assertEqual(geometry, {"width": 1920, "height": 1080, "x": 0, "y": 0, "maximized": False})

    def test_bridge_persists_native_window_state(self) -> None:
        class FakeSettings:
            def __init__(self):
                self.patch = None

            def save(self, patch):
                self.patch = dict(patch)
                return self.patch

        settings = FakeSettings()
        bridge = DesktopBridge(settings_store=settings)
        self.assertTrue(
            bridge.save_window_state(
                {
                    "window_width": 1280,
                    "window_height": 720,
                    "window_left": 10,
                    "window_top": 20,
                    "window_maximized": False,
                    "unexpected": "ignored",
                }
            )
        )
        self.assertEqual(
            settings.patch,
            {
                "window_width": 1280,
                "window_height": 720,
                "window_left": 10,
                "window_top": 20,
                "window_maximized": False,
            },
        )

    def test_native_close_requires_webview_acknowledgement(self) -> None:
        class FakeWindow:
            def __init__(self):
                self.evaluated = []
                self.destroyed = 0

            def evaluate_js(self, script):
                self.evaluated.append(script)

            def destroy(self):
                self.destroyed += 1

        bridge = DesktopBridge()
        window = FakeWindow()
        bridge._window = window
        bridge._run_async = lambda callback: callback()
        self.assertFalse(bridge.handle_closing())
        self.assertEqual(len(window.evaluated), 1)
        self.assertFalse(bridge.handle_closing())
        self.assertEqual(len(window.evaluated), 1)
        self.assertTrue(bridge.native_close_ready(True))
        time.sleep(0.1)
        self.assertEqual(window.destroyed, 1)
        self.assertTrue(bridge.handle_closing())

        cancelled = DesktopBridge()
        cancelled._window = FakeWindow()
        cancelled._close_in_progress = True
        self.assertFalse(cancelled.native_close_ready(False, "", True))
        self.assertEqual(cancelled._window.destroyed, 0)

    def test_recovery_preserves_duplicate_logical_image_references(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RecoveryStore(Path(temporary) / "recovery")
            image = png_data_url()
            result = store.save(
                {
                    "layout": {"canvas": {"width": 720, "height": 2200}},
                    "images": [
                        {"id": "single-background", "name": "same.png", "mime": "image/png", "data_url": image},
                        {"id": "comic-panel-copy", "name": "same.png", "mime": "image/png", "data_url": image},
                    ],
                },
                checkpoint=True,
            )
            self.assertTrue(result["ok"])
            loaded = store.load()
            self.assertEqual(
                [record["id"] for record in loaded["images"]],
                ["single-background", "comic-panel-copy"],
            )
            self.assertEqual(len(list((Path(temporary) / "recovery" / "assets").glob("*"))), 1)

    def test_garbled_font_names_fall_back_to_filename(self) -> None:
        with mock.patch(
            "speech_bubble_editor.font_catalog._font_name_table_text",
            side_effect=["EPSON ????????", "????"],
        ):
            family, style = _font_display_names(
                Path("EPSON-readable-file-name.ttf"),
                "EPSON ????????",
                "????",
            )
        self.assertEqual(family, "EPSON-readable-file-name")
        self.assertEqual(style, "Regular")
        with tempfile.TemporaryDirectory() as temporary:
            invalid = Path(temporary) / "invalid.ttf"
            invalid.write_bytes(b"\0" * 12)
            self.assertFalse(_font_cmap_is_browser_safe(invalid))
        legacy_epson = Path("C:/Windows/Fonts/epgyobld.ttf")
        if legacy_epson.is_file():
            self.assertFalse(_font_cmap_is_browser_safe(legacy_epson))

    def test_settings_recent_and_project_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = make_paths(root / "app")
            settings = SettingsStore(paths.settings)
            self.assertEqual(settings.load()["theme"], "system")
            self.assertEqual(settings.load()["language"], "auto")
            self.assertFalse(settings.load()["show_empty_canvas_guide"])
            self.assertTrue(settings.load()["shared_project_images"])
            self.assertEqual(settings.load()["auto_save_interval_seconds"], 30)
            self.assertNotIn("background_removal_history_limit", settings.load())
            settings.path.write_text(
                json.dumps({"window_width": "invalid", "window_height": "invalid"}),
                encoding="utf-8",
            )
            self.assertEqual(settings.load()["window_width"], 1440)
            self.assertEqual(settings.load()["window_height"], 900)
            settings.save({"window_width": 1440, "window_height": 900})
            self.assertEqual(settings.save({"theme": "dark"})["theme"], "dark")
            self.assertEqual(
                settings.save({"auto_save_interval_seconds": 90})[
                    "auto_save_interval_seconds"
                ],
                90,
            )
            self.assertEqual(
                settings.save({"auto_save_interval_seconds": 9999})[
                    "auto_save_interval_seconds"
                ],
                3600,
            )
            self.assertNotIn(
                "background_removal_history_limit",
                settings.save({"background_removal_history_limit": 999}),
            )

            project_path = root / "sample.sbeproj"
            payload = {
                "title": "sample",
                "layout": current_layout(
                    active_workspace="comic",
                    comic={"version": 1, "enabled": True, "template_id": "vertical_four"},
                ),
                "images": [
                    {
                        "id": "image-1",
                        "name": "panel.png",
                        "mime": "image/png",
                        "data_url": png_data_url(),
                    }
                ],
            }
            saved = ProjectStore().save(project_path, payload)
            loaded = ProjectStore().load(project_path)
            self.assertTrue(saved["ok"])
            self.assertEqual(loaded["layout"]["canvas"], {"width": 720, "height": 1600})
            self.assertEqual(len(loaded["images"]), 1)

            general_path = root / "general-comic.sbeproj"
            general_payload = {
                "title": "general-comic",
                "layout": current_layout(
                    active_workspace="comic_layout",
                    general_elements=[
                        {
                            "id": "general-bubble",
                            "type": "bubble",
                            "general_comic_scope": "panel",
                            "general_comic_panel_id": "general-panel-1",
                        }
                    ],
                    general_comic={
                        "version": 1,
                        "enabled": True,
                        "created": True,
                        "template_id": "standard_five",
                    },
                ),
                "images": [
                    {
                        "id": "general-comic-image:1",
                        "name": "general-panel.png",
                        "mime": "image/png",
                        "data_url": png_data_url(),
                    }
                ],
            }
            ProjectStore().save(general_path, general_payload)
            general_loaded = ProjectStore().load(general_path)
            self.assertEqual(general_loaded["layout"]["version"], 5)
            self.assertEqual(general_loaded["layout"]["active_workspace"], "comic_layout")
            self.assertEqual(general_loaded["layout"]["general_comic"]["template_id"], "standard_five")
            self.assertEqual(general_loaded["images"][0]["id"], "general-comic-image:1")

            duplicate_path = root / "duplicate-image-roles.sbeproj"
            duplicate_payload = {
                **payload,
                "images": [
                    {
                        "id": "__single_background__",
                        "name": "single.png",
                        "mime": "image/png",
                        "data_url": png_data_url(),
                    },
                    {
                        "id": "panel-image-1",
                        "name": "panel.png",
                        "mime": "image/png",
                        "data_url": png_data_url(),
                    },
                ],
            }
            duplicate_saved = ProjectStore().save(duplicate_path, duplicate_payload)
            duplicate_loaded = ProjectStore().load(duplicate_path)
            self.assertEqual(
                [record["id"] for record in duplicate_saved["manifest"]["images"]],
                ["__single_background__", "panel-image-1"],
            )
            self.assertEqual(
                [record["id"] for record in duplicate_loaded["images"]],
                ["__single_background__", "panel-image-1"],
            )
            with zipfile.ZipFile(duplicate_path) as archive:
                self.assertEqual(
                    len([name for name in archive.namelist() if name.startswith("images/")]),
                    1,
                )

            missing_path = root / "missing-image.sbeproj"
            valid_missing_target = ProjectStore().save(missing_path, payload)
            self.assertTrue(valid_missing_target["ok"])
            before_missing = missing_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "Project image blob is missing"):
                ProjectStore().save(
                    missing_path,
                    {
                        **payload,
                        "layout": current_layout(
                            comic_elements=[
                                {"id": "panel-2-image", "type": "image", "image_asset_id": "missing-image"}
                            ],
                            comic={"version": 1, "enabled": True, "template_id": "vertical_four"},
                        ),
                    },
                )
            self.assertEqual(missing_path.read_bytes(), before_missing)

            recent = RecentProjects(paths.recent)
            recent.touch(project_path)
            self.assertEqual(recent.load()[0]["path"], str(project_path.resolve()))

    def test_project_schema_rejects_invalid_archives_without_replacing_valid_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = ProjectStore()
            payload = {
                "title": "schema",
                "layout": current_layout(
                    single_elements=[{"id": "single-image", "type": "image", "image_asset_id": "image-1"}],
                    comic={"version": 1, "enabled": True, "template_id": "vertical_four"},
                ),
                "images": [{"id": "image-1", "name": "image.png", "mime": "image/png", "data_url": png_data_url()}],
            }

            def save_project(name: str) -> Path:
                project_path = root / f"{name}.sbeproj"
                store.save(project_path, payload)
                return project_path

            def rewrite_json(project_path: Path, mutate) -> None:
                with zipfile.ZipFile(project_path, "r") as archive:
                    entries = {entry.filename: archive.read(entry.filename) for entry in archive.infolist()}
                mutate(entries)
                with zipfile.ZipFile(project_path, "w") as archive:
                    for name, data in entries.items():
                        archive.writestr(name, data)

            valid_path = save_project("valid")
            self.assertEqual(store.load(valid_path)["manifest"]["version"], 1)

            future_layout = save_project("future-layout")
            rewrite_json(
                future_layout,
                lambda entries: entries.__setitem__(
                    "layout.json",
                    json.dumps({**json.loads(entries["layout.json"]), "version": 999}).encode("utf-8"),
                ),
            )
            with self.assertRaises(ValueError):
                store.load(future_layout)

            future_comic = save_project("future-comic")
            def mutate_future_comic(entries: dict[str, bytes]) -> None:
                layout = json.loads(entries["layout.json"])
                layout["comic"]["version"] = 999
                entries["layout.json"] = json.dumps(layout).encode("utf-8")
                comic = json.loads(entries["comic.json"])
                comic["version"] = 999
                entries["comic.json"] = json.dumps(comic).encode("utf-8")
            rewrite_json(future_comic, mutate_future_comic)
            with self.assertRaises(ValueError):
                store.load(future_comic)

            future_manifest = save_project("future-manifest")
            rewrite_json(
                future_manifest,
                lambda entries: entries.__setitem__(
                    "manifest.json",
                    json.dumps({**json.loads(entries["manifest.json"]), "version": 2}).encode("utf-8"),
                ),
            )
            with self.assertRaises(ValueError):
                store.load(future_manifest)

            nan_layout = current_layout()
            nan_layout["workspaces"]["single"]["canvas"]["width"] = float("nan")
            with self.assertRaises(ValueError):
                store.save(root / "nan.sbeproj", {"layout": nan_layout, "images": []})
            infinity_layout = current_layout()
            infinity_layout["workspaces"]["single"]["canvas"]["width"] = float("inf")
            with self.assertRaises(ValueError):
                store.save(root / "infinity.sbeproj", {"layout": infinity_layout, "images": []})

            duplicate_images = {**payload, "images": [payload["images"][0], {**payload["images"][0]}]}
            with self.assertRaisesRegex(ValueError, "Duplicate project image id"):
                store.save(root / "duplicate-id.sbeproj", duplicate_images)

            missing_reference = save_project("missing-reference")
            def mutate_missing_reference(entries: dict[str, bytes]) -> None:
                layout = json.loads(entries["layout.json"])
                layout["workspaces"]["single"]["elements"][0]["image_asset_id"] = "missing-image"
                entries["layout.json"] = json.dumps(layout).encode("utf-8")
            rewrite_json(missing_reference, mutate_missing_reference)
            with self.assertRaisesRegex(ValueError, "Project image blob is missing"):
                store.load(missing_reference)

            mismatched_comic = save_project("mismatched-comic")
            rewrite_json(
                mismatched_comic,
                lambda entries: entries.__setitem__("comic.json", json.dumps({"version": 1, "enabled": False}).encode("utf-8")),
            )
            with self.assertRaisesRegex(ValueError, "comic data is inconsistent"):
                store.load(mismatched_comic)

            checksum_mismatch = save_project("checksum-mismatch")
            with zipfile.ZipFile(checksum_mismatch, "r") as archive:
                image_entry = json.loads(archive.read("manifest.json"))["images"][0]["path"]
            rewrite_json(checksum_mismatch, lambda entries: entries.__setitem__(image_entry, b"changed-image"))
            with self.assertRaisesRegex(ValueError, "checksum"):
                store.load(checksum_mismatch)

            undecodable_image = save_project("undecodable-image")
            def mutate_undecodable_image(entries: dict[str, bytes]) -> None:
                manifest = json.loads(entries["manifest.json"])
                image_path = manifest["images"][0]["path"]
                data = b"not an image"
                entries[image_path] = data
                manifest["images"][0]["sha256"] = hashlib.sha256(data).hexdigest()
                entries["manifest.json"] = json.dumps(manifest).encode("utf-8")
            rewrite_json(undecodable_image, mutate_undecodable_image)
            with self.assertRaisesRegex(ValueError, "cannot be decoded"):
                store.load(undecodable_image)

            unchanged = save_project("preserved-output")
            before = unchanged.read_bytes()
            with self.assertRaises(ValueError):
                store.save(unchanged, {"layout": current_layout(), "images": [{"id": "missing", "name": "bad", "mime": "image/png", "data_url": "data:image/png;base64,not-base64"}]})
            self.assertEqual(unchanged.read_bytes(), before)

    def test_recovery_skips_future_layout_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = RecoveryStore(Path(temporary) / "recovery")
            payload = {"layout": current_layout(), "images": [], "checkpoint": True}
            store.save(payload, checkpoint=True)
            record = json.loads(store.current.read_text(encoding="utf-8"))
            record["layout"]["version"] = 999
            store.current.write_text(json.dumps(record), encoding="utf-8")
            restored = store.load()
            self.assertTrue(restored["available"] if "available" in restored else restored["ok"])
            self.assertEqual(restored["fallback_generation"], 1)
            self.assertEqual(restored["layout"]["version"], 5)

    def test_unsafe_project_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_path = Path(temporary) / "unsafe.sbeproj"
            with zipfile.ZipFile(project_path, "w") as archive:
                archive.writestr("../outside.txt", b"unsafe")
                archive.writestr(
                    "manifest.json",
                    json.dumps(
                        {
                            "format": "speech-bubble-editor-project",
                            "version": 1,
                            "layout": "layout.json",
                            "images": [],
                        }
                    ),
                )
                archive.writestr("layout.json", "{}")
            with self.assertRaisesRegex(ValueError, "unsafe path"):
                ProjectStore().load(project_path)

    def test_desktop_routes_require_launch_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = make_paths(Path(temporary) / "app")
            client = TestClient(create_app(paths, "desktop-test-token"))
            self.assertEqual(client.get("/desktop/health").status_code, 403)
            response = client.get(
                "/desktop/health",
                headers={"X-SBE-Token": "desktop-test-token"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["host"], "desktop")
            self.assertEqual(
                client.get("/speech_bubble/fonts").status_code,
                403,
            )

    def test_background_removal_model_status_is_token_protected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = make_paths(Path(temporary) / "app")
            client = TestClient(create_app(paths, "desktop-test-token"))
            self.assertEqual(client.get("/desktop/background-removal/model").status_code, 403)
            response = client.get(
                "/desktop/background-removal/model",
                headers={"X-SBE-Token": "desktop-test-token"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["model"], "isnet-anime")
            self.assertFalse(response.json()["ready"])

    def test_background_removal_inference_returns_png_mask(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = make_paths(Path(temporary) / "app")
            client = TestClient(create_app(paths, "desktop-test-token"))
            output = io.BytesIO()
            Image.new("L", (2, 2), 255).save(output, format="PNG")
            with mock.patch(
                "desktop_app.background_removal.BackgroundRemovalService.infer_mask",
                return_value=(output.getvalue(), 2, 2),
            ):
                response = client.post(
                    "/desktop/background-removal/infer",
                    headers={"X-SBE-Token": "desktop-test-token", "Content-Type": "image/png"},
                    content=base64.b64decode(png_data_url().split(",", 1)[1]),
                )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.headers["content-type"], "image/png")
            self.assertEqual(response.headers["x-sbe-image-width"], "2")
            self.assertEqual(response.headers["x-sbe-image-height"], "2")

    def test_desktop_redirect_uses_saved_runtime_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = make_paths(Path(temporary) / "app")
            SettingsStore(paths.settings).save(
                {
                    "theme": "light",
                    "language": "en",
                    "auto_save": False,
                    "auto_save_interval_seconds": 90,
                    "startup_behavior": "resume",
                    "show_empty_canvas_guide": False,
                }
            )
            client = TestClient(create_app(paths, "desktop-test-token"))
            response = client.get("/", follow_redirects=False)
            query = parse_qs(urlparse(response.headers["location"]).query)
            self.assertEqual(query["theme"], ["light"])
            self.assertEqual(query["language"], ["en"])
            self.assertEqual(query["autoSave"], ["0"])
            self.assertEqual(query["autoSaveDelay"], ["90000"])
            self.assertNotIn("backgroundRemovalHistoryLimit", query)
            self.assertEqual(query["startupBehavior"], ["resume"])
            self.assertEqual(query["showEmptyCanvasGuide"], ["0"])

    def test_desktop_recovery_routes_survive_app_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = make_paths(Path(temporary) / "app")
            headers = {"X-SBE-Token": "desktop-test-token"}
            payload = {
                "title": "restart",
                "layout": {"canvas": {"width": 720, "height": 2160}, "comic": {"enabled": True}},
                "images": [{"id": "image-1", "name": "panel.png", "mime": "image/png", "data_url": png_data_url()}],
                "checkpoint": True,
            }
            first = TestClient(create_app(paths, "desktop-test-token"))
            saved = first.post("/desktop/recovery/save", headers=headers, json=payload)
            self.assertEqual(saved.status_code, 200, saved.text)

            second = TestClient(create_app(paths, "desktop-test-token"))
            loaded = second.get("/desktop/recovery/load", headers=headers)
            self.assertEqual(loaded.status_code, 200, loaded.text)
            self.assertEqual(loaded.json()["layout"]["canvas"], {"width": 720, "height": 2160})
            self.assertEqual(len(loaded.json()["images"]), 1)

    def test_desktop_export_writes_to_selected_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = make_paths(root / "app")
            output = root / "selected-output"
            output.mkdir()
            SettingsStore(paths.settings).save({"output_format": "png"})
            client = TestClient(create_app(paths, "desktop-test-token"))
            response = client.post(
                "/speech-bubble-editor/export",
                headers={"X-SBE-Token": "desktop-test-token"},
                json={
                    "image_data_url": png_data_url(),
                    "layout_json": "{}",
                    "name": "selected",
                    "desktop_output_dir": str(output),
                },
            )
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertTrue(payload["desktop_output"])
            self.assertIsNone(payload["download_url"])
            self.assertTrue((Path(payload["output_dir"]) / payload["filename"]).is_file())

    def test_user_sfx_preset_can_be_created_and_reedited(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = make_paths(Path(temporary) / "app")
            client = TestClient(create_app(paths, "desktop-test-token"))
            headers = {"X-SBE-Token": "desktop-test-token"}
            created = client.post(
                "/speech-bubble-editor/user-assets",
                headers=headers,
                json={
                    "category": "stamp",
                    "name": "mission",
                    "image_data_url": png_data_url(),
                    "allow_opaque": True,
                    "resize_oversize": False,
                    "conflict": "error",
                    "style_defaults": {
                        "fill": "#ff0000",
                        "stroke": "#ffffff",
                        "stroke_width": 2,
                        "shadow_enabled": True,
                        "glow_enabled": True,
                    },
                },
            )
            self.assertEqual(created.status_code, 200, created.text)
            preset = created.json()["preset"]
            updated = client.patch(
                f"/speech-bubble-editor/user-assets/{preset['id']}",
                headers=headers,
                json={
                    "name": "mission complete",
                    "category": "stamp",
                    "conflict": "error",
                    "style_defaults": {
                        **preset["style_defaults"],
                        "fill": "#00ff00",
                        "glow_spread": 8,
                    },
                },
            )
            self.assertEqual(updated.status_code, 200, updated.text)
            self.assertEqual(updated.json()["preset"]["name"], "mission complete")
            self.assertEqual(updated.json()["preset"]["style_defaults"]["fill"], "#00ff00")


if __name__ == "__main__":
    unittest.main()
