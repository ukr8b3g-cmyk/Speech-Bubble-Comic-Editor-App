from __future__ import annotations

import base64
import hashlib
import io
import os
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from PIL import Image

from .project_schema import (
    PROJECT_ARCHIVE_VERSION,
    PROJECT_FORMAT,
    ProjectSchemaError,
    json_bytes,
    strict_json_loads,
    validate_comic_state,
    validate_layout,
    validate_manifest,
    validate_unique_logical_ids,
)
from .version import APP_VERSION

MAX_PROJECT_BYTES = 512 * 1024 * 1024
MAX_ENTRIES = 256
MAX_IMAGE_BYTES = 96 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}


def _safe_entries(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    entries = archive.infolist()
    if len(entries) > MAX_ENTRIES:
        raise ValueError("Project contains too many files")
    total = 0
    names = set()
    for info in entries:
        path = PurePosixPath(info.filename)
        if info.filename in names or path.is_absolute() or ".." in path.parts or "\\" in info.filename:
            raise ValueError("Project contains an unsafe path")
        names.add(info.filename)
        total += max(0, info.file_size)
        if total > MAX_PROJECT_BYTES:
            raise ValueError("Project is too large")
    return entries


def _inspect_project_image(data: bytes) -> tuple[str, int, int]:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Project image is empty or too large")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
            image_format = str(image.format or "").upper()
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
    except Exception as error:
        raise ValueError("Project image cannot be decoded") from error
    if image_format not in ALLOWED_IMAGE_FORMATS or width * height > 100_000_000:
        raise ValueError("Project image format or dimensions are unsupported")
    return image_format, width, height


def _decode_project_image(record: dict) -> tuple[str, bytes, dict]:
    if not isinstance(record, dict):
        raise ValueError("Project image record is invalid")
    raw = str(record.get("data_url", ""))
    if "," not in raw:
        raise ValueError("Project image data is missing")
    encoded = raw.split(",", 1)[1]
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError("Project image data is invalid") from error
    image_format, width, height = _inspect_project_image(data)
    image_id = str(record.get("id") or "").strip()
    if not image_id:
        raise ValueError("Project image id is missing")
    extension = ALLOWED_IMAGE_FORMATS[image_format]
    digest = hashlib.sha256(data).hexdigest()
    metadata = {
        "id": image_id,
        # The archive blob is content-addressed, while each manifest record
        # keeps its own logical id (panel image, single background, and so on).
        "path": f"images/{digest}.{extension}",
        "original_name": str(record.get("name") or f"{image_id}.{extension}")[:260],
        "mime": f"image/{'jpeg' if extension == 'jpg' else extension}",
        "width": width,
        "height": height,
        "sha256": digest,
    }
    return metadata["path"], data, metadata


_LAYOUT_IMAGE_KEYS = {"image_id", "imageId", "background_image_id", "backgroundImageId", "image_asset_id"}


def _referenced_image_ids(value, path: str = "layout") -> list[tuple[str, str]]:
    """Return logical image references while retaining a useful layout path."""
    references: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in _LAYOUT_IMAGE_KEYS and isinstance(child, str) and child and child != "source":
                references.append((child, child_path))
            references.extend(_referenced_image_ids(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            references.extend(_referenced_image_ids(child, f"{path}[{index}]"))
    return references


class ProjectStore:
    def save(self, path: Path, payload: dict) -> dict:
        target = path.with_suffix(".sbeproj")
        target.parent.mkdir(parents=True, exist_ok=True)
        layout = payload.get("layout")
        if isinstance(layout, str):
            layout = strict_json_loads(layout or "{}", label="layout")
        if not isinstance(layout, dict):
            raise ValueError("Project layout is invalid")
        layout = validate_layout(layout, require_current=True)
        comic = layout.get("comic") if isinstance(layout.get("comic"), dict) else {}
        validate_comic_state(comic)
        source_images = payload.get("images")
        if not isinstance(source_images, list):
            raise ValueError("Project image list is invalid")
        images = []
        image_files = {}
        for record in source_images:
            entry_path, data, metadata = _decode_project_image(record)
            images.append(metadata)
            image_files.setdefault(entry_path, data)
        validate_unique_logical_ids(images)
        image_ids = {str(item["id"]) for item in images}
        missing = [(image_id, location) for image_id, location in _referenced_image_ids(layout) if image_id not in image_ids]
        if missing:
            details = ", ".join(f"{image_id} ({location})" for image_id, location in missing[:8])
            suffix = "" if len(missing) <= 8 else f" (+{len(missing) - 8} more)"
            raise ValueError(f"Project image blob is missing: {details}{suffix}")
        now = datetime.now(timezone.utc).isoformat()
        manifest = {
            "format": PROJECT_FORMAT,
            "version": PROJECT_ARCHIVE_VERSION,
            "app_version": APP_VERSION,
            "layout_schema_version": int(layout.get("version", 1)),
            "comic_schema_version": int(comic.get("version", 1)) if comic else None,
            "created_at": str(payload.get("created_at") or now),
            "updated_at": now,
            "project_id": str(payload.get("project_id") or uuid.uuid4()),
            "title": str(payload.get("title") or target.stem)[:260],
            "page": {
                "width": int(layout.get("canvas", {}).get("width", 1024)),
                "height": int(layout.get("canvas", {}).get("height", 1024)),
            },
            "layout": "layout.json",
            "comic": "comic.json",
            "images": images,
        }
        manifest = validate_manifest(manifest)
        handle, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        os.close(handle)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                archive.writestr("manifest.json", json_bytes(manifest))
                archive.writestr("layout.json", json_bytes(layout))
                archive.writestr("comic.json", json_bytes(comic))
                for entry_path, data in image_files.items():
                    archive.writestr(entry_path, data)
            with zipfile.ZipFile(temporary, "r") as archive:
                _safe_entries(archive)
                written_manifest = validate_manifest(strict_json_loads(archive.read("manifest.json"), label="manifest"))
                written_layout = validate_layout(strict_json_loads(archive.read("layout.json"), label="layout"), require_current=True)
                written_comic = validate_comic_state(strict_json_loads(archive.read(written_manifest["comic"]), label="comic state"))
                if written_layout.get("comic", {}) != written_comic:
                    raise ProjectSchemaError("Project comic data is inconsistent")
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return {"ok": True, "path": str(target), "manifest": manifest}

    def load(self, path: Path) -> dict:
        if not path.is_file() or path.stat().st_size > MAX_PROJECT_BYTES:
            raise ValueError("Project file is missing or too large")
        with zipfile.ZipFile(path, "r") as archive:
            _safe_entries(archive)
            manifest = validate_manifest(strict_json_loads(archive.read("manifest.json"), label="manifest"))
            layout = validate_layout(strict_json_loads(archive.read(manifest["layout"]), label="layout"))
            archive_names = {entry.filename for entry in archive.infolist()}
            comic_path = manifest.get("comic") or ("comic.json" if "comic.json" in archive_names else "")
            if manifest.get("comic") and comic_path not in archive_names:
                raise ValueError("Project comic data is missing")
            if comic_path:
                archived_comic = validate_comic_state(strict_json_loads(archive.read(comic_path), label="comic state"))
                layout_comic = layout.get("comic")
                if isinstance(layout_comic, dict):
                    if layout_comic != archived_comic:
                        raise ValueError("Project comic data is inconsistent")
                elif archived_comic:
                    layout["comic"] = archived_comic
            images = []
            for record in manifest["images"]:
                entry = record["path"]
                data = archive.read(entry)
                if hashlib.sha256(data).hexdigest() != record.get("sha256"):
                    raise ValueError("Project image checksum does not match")
                image_format, width, height = _inspect_project_image(data)
                extension = ALLOWED_IMAGE_FORMATS[image_format]
                actual_mime = f"image/{'jpeg' if extension == 'jpg' else extension}"
                if record["mime"] != actual_mime or int(record["width"]) != width or int(record["height"]) != height:
                    raise ValueError("Project image metadata does not match")
                images.append(
                    {
                        "id": record["id"],
                        "name": record.get("original_name", record["id"]),
                        "mime": record.get("mime", "image/png"),
                        "data_url": f"data:{record.get('mime', 'image/png')};base64,{base64.b64encode(data).decode('ascii')}",
                    }
                )
            image_ids = {record["id"] for record in manifest["images"]}
            missing = [(image_id, location) for image_id, location in _referenced_image_ids(layout) if image_id not in image_ids]
            if missing:
                details = ", ".join(f"{image_id} ({location})" for image_id, location in missing[:8])
                suffix = "" if len(missing) <= 8 else f" (+{len(missing) - 8} more)"
                raise ValueError(f"Project image blob is missing: {details}{suffix}")
        return {"ok": True, "path": str(path), "manifest": manifest, "layout": layout, "images": images}
