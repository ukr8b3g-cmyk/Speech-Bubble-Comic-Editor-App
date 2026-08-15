from __future__ import annotations

import json
import math
import re
from pathlib import PurePosixPath


PROJECT_FORMAT = "speech-bubble-editor-project"
PROJECT_ARCHIVE_VERSION = 1
LAYOUT_FORMAT = "speech-bubble-editor-layout"
LAYOUT_SCHEMA_VERSION = 5
COMIC_SCHEMA_VERSION = 1
GENERAL_COMIC_SCHEMA_VERSION = 1
RECOVERY_FORMAT = "speech-bubble-editor-recovery"
RECOVERY_VERSION = 1
MAX_LAYOUT_BYTES = 32 * 1024 * 1024
ALLOWED_IMAGE_MIMES = {"image/png", "image/jpeg", "image/webp"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)


class ProjectSchemaError(ValueError):
    pass


def _reject_json_constant(value: str):
    raise ProjectSchemaError(f"Non-finite JSON number is not allowed: {value}")


def strict_json_loads(raw: str | bytes, *, label: str) -> dict:
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        value = json.loads(raw, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ProjectSchemaError) as error:
        if isinstance(error, ProjectSchemaError):
            raise
        raise ProjectSchemaError(f"{label} JSON is invalid") from error
    if not isinstance(value, dict):
        raise ProjectSchemaError(f"{label} JSON must contain an object")
    return value


def json_bytes(value: dict) -> bytes:
    if not isinstance(value, dict):
        raise ProjectSchemaError("JSON value must be an object")
    try:
        return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ProjectSchemaError("JSON value cannot be serialized") from error


def _clone_object(value: dict, *, label: str) -> dict:
    return strict_json_loads(json_bytes(value), label=label)


def _positive_integer(value: object, *, label: str, maximum: int) -> int:
    if isinstance(value, bool):
        raise ProjectSchemaError(f"{label} is invalid")
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ProjectSchemaError(f"{label} is invalid") from error
    if number < 1 or number > maximum or str(value).strip() not in {str(number), ""}:
        raise ProjectSchemaError(f"{label} is invalid or unsupported")
    return number


def _finite_dimension(value: object, *, label: str) -> None:
    if isinstance(value, bool):
        raise ProjectSchemaError(f"{label} must be a finite number of at least 1")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ProjectSchemaError(f"{label} must be a finite number of at least 1") from error
    if not math.isfinite(number) or number < 1:
        raise ProjectSchemaError(f"{label} must be a finite number of at least 1")


def _safe_relative_posix_path(value: object, *, label: str) -> str:
    path_text = str(value or "")
    path = PurePosixPath(path_text)
    if not path_text or path.is_absolute() or ".." in path.parts or "\\" in path_text:
        raise ProjectSchemaError(f"{label} must be a safe relative POSIX path")
    return path.as_posix()


def _validate_canvas(value: object, *, label: str) -> None:
    if not isinstance(value, dict):
        raise ProjectSchemaError(f"{label} canvas is invalid")
    _finite_dimension(value.get("width"), label=f"{label}.canvas.width")
    _finite_dimension(value.get("height"), label=f"{label}.canvas.height")


def _validate_elements(value: object, *, label: str) -> None:
    if not isinstance(value, list):
        raise ProjectSchemaError(f"{label} elements must be an array")
    ids: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            continue
        item_id = item_id.strip()
        if item_id in ids:
            raise ProjectSchemaError(f"Duplicate layer id in {label}: {item_id}")
        ids.add(item_id)


def validate_comic_state(comic: object) -> dict:
    if comic is None:
        return {}
    if not isinstance(comic, dict):
        raise ProjectSchemaError("Comic state must be an object")
    result = _clone_object(comic, label="comic state")
    version = result.get("version", COMIC_SCHEMA_VERSION)
    _positive_integer(version, label="Comic state version", maximum=COMIC_SCHEMA_VERSION)
    return result


def validate_general_comic_state(comic: object) -> dict:
    if comic is None:
        return {}
    if not isinstance(comic, dict):
        raise ProjectSchemaError("General comic state must be an object")
    result = _clone_object(comic, label="general comic state")
    version = result.get("version", GENERAL_COMIC_SCHEMA_VERSION)
    _positive_integer(
        version,
        label="General comic state version",
        maximum=GENERAL_COMIC_SCHEMA_VERSION,
    )
    return result


def validate_layout(layout: dict, *, require_current: bool = False) -> dict:
    if not isinstance(layout, dict):
        raise ProjectSchemaError("Project layout is invalid")
    raw = json_bytes(layout)
    if len(raw) > MAX_LAYOUT_BYTES:
        raise ProjectSchemaError("Project layout is too large")
    result = strict_json_loads(raw, label="layout")
    version_value = result.get("version")
    version = None if version_value is None else _positive_integer(
        version_value,
        label="Layout version",
        maximum=LAYOUT_SCHEMA_VERSION,
    )
    if require_current and version != LAYOUT_SCHEMA_VERSION:
        raise ProjectSchemaError(f"Layout version {LAYOUT_SCHEMA_VERSION} is required for saving")
    if version == LAYOUT_SCHEMA_VERSION:
        if result.get("format") not in {None, LAYOUT_FORMAT}:
            raise ProjectSchemaError("Project layout format is invalid")
        active_workspace = result.get("active_workspace")
        if active_workspace not in {"single", "comic", "comic_layout"}:
            raise ProjectSchemaError("Project active workspace is invalid")
        workspaces = result.get("workspaces")
        if not isinstance(workspaces, dict):
            raise ProjectSchemaError("Project workspaces are invalid")
        for name in ("single", "comic", "comic_layout"):
            workspace = workspaces.get(name)
            if not isinstance(workspace, dict):
                raise ProjectSchemaError(f"Project workspace is missing: {name}")
            _validate_canvas(workspace.get("canvas"), label=f"workspaces.{name}")
            _validate_elements(workspace.get("elements"), label=f"workspaces.{name}")
    else:
        if "canvas" in result:
            _validate_canvas(result.get("canvas"), label="layout")
        if "elements" in result:
            _validate_elements(result.get("elements"), label="layout")
    if "comic" in result and result.get("comic") is not None:
        validate_comic_state(result["comic"])
    if "general_comic" in result and result.get("general_comic") is not None:
        validate_general_comic_state(result["general_comic"])
    return result


def validate_unique_logical_ids(records: list[dict]) -> None:
    ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ProjectSchemaError("Project image record is invalid")
        image_id = record.get("id")
        if not isinstance(image_id, str) or not image_id.strip():
            raise ProjectSchemaError("Project image id is invalid")
        image_id = image_id.strip()
        if image_id in ids:
            raise ProjectSchemaError(f"Duplicate project image id: {image_id}")
        ids.add(image_id)


def validate_image_manifest_records(records: object) -> list[dict]:
    if not isinstance(records, list):
        raise ProjectSchemaError("Project image manifest is invalid")
    result = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ProjectSchemaError(f"Project image manifest record {index} is invalid")
        copied = _clone_object(record, label=f"project image manifest record {index}")
        image_id = copied.get("id")
        if not isinstance(image_id, str) or not image_id.strip():
            raise ProjectSchemaError("Project image id is invalid")
        copied["id"] = image_id.strip()
        copied["path"] = _safe_relative_posix_path(copied.get("path"), label="Project image path")
        mime = str(copied.get("mime") or "").lower()
        if mime not in ALLOWED_IMAGE_MIMES:
            raise ProjectSchemaError("Project image MIME type is invalid")
        copied["mime"] = mime
        _finite_dimension(copied.get("width"), label="Project image width")
        _finite_dimension(copied.get("height"), label="Project image height")
        digest = str(copied.get("sha256") or "")
        if not _SHA256_RE.fullmatch(digest):
            raise ProjectSchemaError("Project image checksum is invalid")
        copied["sha256"] = digest.lower()
        result.append(copied)
    validate_unique_logical_ids(result)
    return result


def validate_manifest(manifest: dict) -> dict:
    if not isinstance(manifest, dict):
        raise ProjectSchemaError("Project manifest is invalid")
    result = _clone_object(manifest, label="manifest")
    if result.get("format") != PROJECT_FORMAT:
        raise ProjectSchemaError("Project format is unsupported")
    _positive_integer(
        result.get("version"),
        label="Project archive version",
        maximum=PROJECT_ARCHIVE_VERSION,
    )
    result["layout"] = _safe_relative_posix_path(result.get("layout", "layout.json"), label="Project layout path")
    if result.get("comic") is not None:
        result["comic"] = _safe_relative_posix_path(result["comic"], label="Project comic path")
    result["images"] = validate_image_manifest_records(result.get("images"))
    return result
