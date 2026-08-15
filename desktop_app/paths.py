from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


def resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).resolve()  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DesktopPaths:
    root: Path
    settings: Path
    recent: Path
    recovery: Path
    cache: Path
    logs: Path
    temp: Path
    models: Path

    @classmethod
    def create(cls, portable: bool = False) -> "DesktopPaths":
        if portable:
            root = resource_root() / "data"
        else:
            local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
            root = local / "SpeechBubbleComicEditorApp"
        value = cls(
            root=root,
            settings=root / "settings.json",
            recent=root / "recent.json",
            recovery=root / "recovery",
            cache=root / "cache",
            logs=root / "logs",
            temp=root / "temp",
            models=root / "models",
        )
        for directory in (value.root, value.recovery, value.cache, value.logs, value.temp, value.models):
            directory.mkdir(parents=True, exist_ok=True)
        return value
