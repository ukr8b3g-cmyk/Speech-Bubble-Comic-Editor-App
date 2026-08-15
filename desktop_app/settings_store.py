from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


DEFAULTS = {
    "version": 1,
    "window_width": 1440,
    "window_height": 900,
    "window_left": None,
    "window_top": None,
    "window_maximized": True,
    "theme": "system",
    "language": "auto",
    "show_empty_canvas_guide": False,
    "shared_project_images": True,
    "supersample": 2,
    "last_project_directory": "",
    "export_directory": "",
    "last_export_directory": "",
    "auto_export_to_directory": False,
    "remember_export_directory": True,
    "startup_behavior": "ask",
    "auto_save": True,
    "auto_save_interval_seconds": 30,
    "output_format": "png",
    "png_compression": 6,
    "jpeg_quality": 95,
    "webp_quality": 90,
    "webp_lossless": False,
    "filename_format": "source_datetime",
    "date_subfolder": "none",
    "backup_enabled": True,
    "backup_generations": 5,
    "save_overlay": False,
}


def _bounded_int(value, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _atomic_json_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class SettingsStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            value = {}
        merged = {**DEFAULTS, **(value if isinstance(value, dict) else {})}
        merged.pop("background_removal_history_limit", None)
        merged["window_width"] = _bounded_int(merged.get("window_width"), 1440, 900, 3840)
        merged["window_height"] = _bounded_int(merged.get("window_height"), 900, 640, 2160)
        for key in ("window_left", "window_top"):
            raw = merged.get(key)
            try:
                merged[key] = int(raw) if raw is not None else None
            except (TypeError, ValueError):
                merged[key] = None
        maximized = merged.get("window_maximized", True)
        if isinstance(maximized, str):
            maximized = maximized.strip().lower() in {"1", "true", "yes", "on"}
        merged["window_maximized"] = bool(maximized)
        merged["theme"] = merged["theme"] if merged["theme"] in {"system", "dark", "light"} else "system"
        merged["language"] = merged["language"] if merged["language"] in {"auto", "ja", "en"} else "auto"
        merged["show_empty_canvas_guide"] = bool(merged.get("show_empty_canvas_guide", False))
        merged["shared_project_images"] = bool(merged.get("shared_project_images", True))
        merged["supersample"] = _bounded_int(merged.get("supersample"), 2, 1, 4)
        merged["export_directory"] = str(merged.get("export_directory", "") or "").strip()
        merged["last_export_directory"] = str(merged.get("last_export_directory", "") or "").strip()
        merged["auto_export_to_directory"] = bool(merged.get("auto_export_to_directory", False))
        merged["remember_export_directory"] = bool(merged.get("remember_export_directory", True))
        merged["startup_behavior"] = (
            merged["startup_behavior"]
            if merged.get("startup_behavior") in {"ask", "resume", "new"}
            else "ask"
        )
        merged["auto_save"] = bool(merged.get("auto_save", True))
        merged["auto_save_interval_seconds"] = _bounded_int(
            merged.get("auto_save_interval_seconds"), 30, 5, 3600
        )
        merged["output_format"] = (
            merged["output_format"]
            if merged.get("output_format") in {"png", "jpeg", "webp"}
            else "png"
        )
        merged["png_compression"] = _bounded_int(merged.get("png_compression"), 6, 0, 9)
        merged["jpeg_quality"] = _bounded_int(merged.get("jpeg_quality"), 95, 1, 100)
        merged["webp_quality"] = _bounded_int(merged.get("webp_quality"), 90, 1, 100)
        merged["webp_lossless"] = bool(merged.get("webp_lossless", False))
        merged["filename_format"] = (
            merged["filename_format"]
            if merged.get("filename_format")
            in {"source_datetime", "source_sequence", "source_only", "speech_bubble_datetime"}
            else "source_datetime"
        )
        merged["date_subfolder"] = (
            merged["date_subfolder"]
            if merged.get("date_subfolder") in {"none", "year_month", "year_month_day"}
            else "none"
        )
        merged["backup_enabled"] = bool(merged.get("backup_enabled", True))
        merged["backup_generations"] = _bounded_int(merged.get("backup_generations"), 5, 1, 20)
        merged["save_overlay"] = bool(merged.get("save_overlay", False))
        return merged

    def save(self, patch: dict) -> dict:
        current = self.load()
        current.update({key: value for key, value in patch.items() if key in DEFAULTS})
        normalized = {**DEFAULTS, **current}
        _atomic_json_write(self.path, normalized)
        return self.load()
