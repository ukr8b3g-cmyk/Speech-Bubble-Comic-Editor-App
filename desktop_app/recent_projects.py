from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .settings_store import _atomic_json_write


class RecentProjects:
    def __init__(self, path: Path, limit: int = 10):
        self.path = path
        self.limit = limit

    def load(self) -> list[dict]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            items = payload.get("items", [])
        except (OSError, ValueError, TypeError):
            items = []
        result = []
        for item in items if isinstance(items, list) else []:
            path = Path(str(item.get("path", "")))
            if path.is_file():
                result.append(
                    {
                        "path": str(path),
                        "name": path.name,
                        "last_opened_at": str(item.get("last_opened_at", "")),
                    }
                )
        return result[: self.limit]

    def touch(self, path: Path) -> list[dict]:
        resolved = path.resolve()
        items = [item for item in self.load() if Path(item["path"]).resolve() != resolved]
        items.insert(
            0,
            {
                "path": str(resolved),
                "name": resolved.name,
                "last_opened_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        _atomic_json_write(self.path, {"version": 1, "items": items[: self.limit]})
        return items[: self.limit]

    def remove(self, raw_path: str) -> list[dict]:
        requested = Path(raw_path).resolve()
        items = [item for item in self.load() if Path(item["path"]).resolve() != requested]
        _atomic_json_write(self.path, {"version": 1, "items": items})
        return items
