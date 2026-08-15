from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .project_schema import (
    ALLOWED_IMAGE_MIMES,
    RECOVERY_FORMAT,
    RECOVERY_VERSION,
    json_bytes,
    strict_json_loads,
    validate_layout,
    validate_unique_logical_ids,
)
from .project_store import _decode_project_image, _inspect_project_image

MAX_GENERATIONS = 5
MAX_AGE_DAYS = 30
MAX_TOTAL_BYTES = 1024 * 1024 * 1024


def _atomic_json_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _parse_time(value: object) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.fromtimestamp(0, timezone.utc)


class RecoveryStore:
    def __init__(self, root: Path):
        self.root = root
        self.assets = root / "assets"
        self.generations = root / "generations"
        self.current = root / "current.json"
        for directory in (self.root, self.assets, self.generations):
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _layout(payload: dict) -> dict:
        layout = payload.get("layout")
        if isinstance(layout, str):
            layout = strict_json_loads(layout or "{}", label="recovery layout")
        if not isinstance(layout, dict):
            raise ValueError("Recovery layout is invalid")
        return validate_layout(layout)

    @staticmethod
    def _validate_asset_records(records: object) -> list[dict]:
        if not isinstance(records, list):
            raise ValueError("Recovery image list is invalid")
        validate_unique_logical_ids(records)
        result = []
        for record in records:
            copied = dict(record)
            filename = str(copied.get("file") or "")
            digest = str(copied.get("sha256") or "").lower()
            mime = str(copied.get("mime") or "").lower()
            if not filename or Path(filename).name != filename or "/" in filename or "\\" in filename:
                raise ValueError("Recovery image file is invalid")
            if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
                raise ValueError("Recovery image checksum is invalid")
            if mime not in ALLOWED_IMAGE_MIMES:
                raise ValueError("Recovery image MIME type is invalid")
            copied["id"] = str(copied["id"]).strip()
            copied["sha256"] = digest
            copied["mime"] = mime
            result.append(copied)
        return result

    def _asset_records(self, payload: dict) -> list[dict]:
        source_records = payload.get("images")
        if not isinstance(source_records, list):
            raise ValueError("Recovery image list is invalid")
        validate_unique_logical_ids(source_records)
        records = []
        for source in source_records:
            _entry, data, metadata = _decode_project_image(source)
            digest = metadata["sha256"]
            extension = Path(metadata["path"]).suffix.lower() or ".png"
            asset_path = self.assets / f"{digest}{extension}"
            if not asset_path.is_file():
                handle, temporary = tempfile.mkstemp(prefix=f".{digest}.", suffix=".tmp", dir=self.assets)
                try:
                    with os.fdopen(handle, "wb") as stream:
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, asset_path)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
            records.append(
                {
                    "id": metadata["id"],
                    "name": metadata["original_name"],
                    "mime": metadata["mime"],
                    "sha256": digest,
                    "file": asset_path.name,
                }
            )
        return records

    @staticmethod
    def _state_hash(layout: dict, images: list[dict], project_path: str = "") -> str:
        value = {
            "layout": layout,
            "project_path": project_path,
            "images": [
                {"id": item["id"], "sha256": item["sha256"], "name": item["name"]}
                for item in images
            ],
        }
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def save(self, payload: dict, *, checkpoint: bool = False) -> dict:
        layout = self._layout(payload)
        images = self._asset_records(payload)
        now = datetime.now(timezone.utc)
        record = {
            "format": RECOVERY_FORMAT,
            "version": RECOVERY_VERSION,
            "updated_at": now.isoformat(),
            "title": str(payload.get("title") or "speech-bubble-project")[:260],
            "project_path": str(payload.get("project_path") or "")[:1024],
            "layout": layout,
            "images": images,
        }
        record["state_hash"] = self._state_hash(layout, images, record["project_path"])
        previous = self._read_record(self.current, validate_assets=False)
        changed = previous.get("state_hash") != record["state_hash"]
        _atomic_json_write(self.current, record)
        generation_created = False
        if checkpoint and changed:
            filename = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{uuid.uuid4().hex[:8]}.json"
            _atomic_json_write(self.generations / filename, record)
            generation_created = True
        cleanup = self.cleanup()
        return {
            "ok": True,
            "changed": changed,
            "generation_created": generation_created,
            "state_hash": record["state_hash"],
            **cleanup,
        }

    def _read_record(self, path: Path, *, validate_assets: bool = True) -> dict:
        try:
            record = strict_json_loads(path.read_bytes(), label="recovery")
            if record.get("format") != RECOVERY_FORMAT or record.get("version") != RECOVERY_VERSION:
                return {}
            record["layout"] = validate_layout(record.get("layout"))
            record["images"] = self._validate_asset_records(record.get("images"))
        except (OSError, ValueError, TypeError):
            return {}
        if validate_assets:
            for image in record.get("images", []):
                asset = self.assets / str(image.get("file", ""))
                if not asset.is_file():
                    return {}
                data = asset.read_bytes()
                if hashlib.sha256(data).hexdigest() != image.get("sha256"):
                    return {}
                try:
                    image_format, _width, _height = _inspect_project_image(data)
                except ValueError:
                    return {}
                extension = {"PNG": "png", "JPEG": "jpeg", "WEBP": "webp"}[image_format]
                if image.get("mime") != f"image/{extension}":
                    return {}
        return record

    def _payload(self, record: dict) -> dict:
        images = []
        for item in record.get("images", []):
            asset = self.assets / str(item["file"])
            images.append(
                {
                    "id": item["id"],
                    "name": item.get("name", item["id"]),
                    "mime": item.get("mime", "image/png"),
                    "data_url": f"data:{item.get('mime', 'image/png')};base64,{base64.b64encode(asset.read_bytes()).decode('ascii')}",
                }
            )
        return {
            "ok": True,
            "manifest": {
                "title": record.get("title", "speech-bubble-project"),
                "updated_at": record.get("updated_at", ""),
                "project_path": record.get("project_path", ""),
                "recovery": True,
            },
            "layout": record["layout"],
            "images": images,
            "state_hash": record.get("state_hash", ""),
        }

    def load(self) -> dict:
        candidates = [self.current, *sorted(self.generations.glob("*.json"), reverse=True)]
        failed = 0
        for path in candidates:
            record = self._read_record(path)
            if record:
                payload = self._payload(record)
                payload["fallback_generation"] = failed
                return payload
            if path.is_file():
                failed += 1
        return {"ok": True, "available": False, "fallback_generation": failed}

    def cleanup(self) -> dict:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=MAX_AGE_DAYS)
        generation_records = []
        for path in self.generations.glob("*.json"):
            record = self._read_record(path, validate_assets=False)
            generation_records.append((path, record, _parse_time(record.get("updated_at"))))
        generation_records.sort(key=lambda item: item[2], reverse=True)
        retained = []
        for index, (path, record, updated) in enumerate(generation_records):
            if index >= MAX_GENERATIONS or updated < cutoff:
                path.unlink(missing_ok=True)
            else:
                retained.append((path, record, updated))

        referenced = set()
        for _path, record, _updated in retained:
            referenced.update(str(item.get("file", "")) for item in record.get("images", []))
        current = self._read_record(self.current, validate_assets=False)
        referenced.update(str(item.get("file", "")) for item in current.get("images", []))
        for asset in self.assets.glob("*"):
            if asset.is_file() and asset.name not in referenced:
                asset.unlink(missing_ok=True)

        files = [path for path in self.root.rglob("*") if path.is_file()]
        total = sum(path.stat().st_size for path in files)
        while total > MAX_TOTAL_BYTES and retained:
            path, _record, _updated = retained.pop()
            path.unlink(missing_ok=True)
            self._remove_unreferenced_assets()
            files = [item for item in self.root.rglob("*") if item.is_file()]
            total = sum(item.stat().st_size for item in files)
        return {"generations": len(retained), "total_size": total}

    def _remove_unreferenced_assets(self) -> None:
        referenced = set()
        for path in [self.current, *self.generations.glob("*.json")]:
            record = self._read_record(path, validate_assets=False)
            referenced.update(str(item.get("file", "")) for item in record.get("images", []))
        for asset in self.assets.glob("*"):
            if asset.is_file() and asset.name not in referenced:
                asset.unlink(missing_ok=True)

    def status(self) -> dict:
        self.cleanup()
        candidates = [self.current, *sorted(self.generations.glob("*.json"), reverse=True)]
        latest = {}
        for path in candidates:
            latest = self._read_record(path)
            if latest:
                break
        files = [path for path in self.root.rglob("*") if path.is_file()]
        return {
            "available": bool(latest),
            "generations": len(list(self.generations.glob("*.json"))),
            "assets": len(list(self.assets.glob("*"))),
            "total_size": sum(path.stat().st_size for path in files),
            "updated_at": latest.get("updated_at", ""),
        }

    def clear(self) -> int:
        files = [path for path in self.root.rglob("*") if path.is_file()]
        count = len(files)
        if self.root.exists():
            shutil.rmtree(self.root)
        for directory in (self.root, self.assets, self.generations):
            directory.mkdir(parents=True, exist_ok=True)
        return count
