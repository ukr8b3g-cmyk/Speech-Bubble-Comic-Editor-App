from __future__ import annotations

import asyncio
import os
import secrets
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from speech_bubble_editor.api import register_routes

from .background_removal import BackgroundRemovalService, MAX_IMAGE_BYTES
from .paths import DesktopPaths
from .project_store import ProjectStore
from .recent_projects import RecentProjects
from .recovery_store import RecoveryStore
from .settings_store import SettingsStore


def create_app(paths: DesktopPaths, launch_token: str | None = None) -> FastAPI:
    token = launch_token or secrets.token_urlsafe(32)
    os.environ["SPEECH_BUBBLE_DESKTOP_DATA_ROOT"] = str(paths.root)
    settings = SettingsStore(paths.settings)
    recent = RecentProjects(paths.recent)
    projects = ProjectStore()
    recovery = RecoveryStore(paths.recovery)
    background_removal = BackgroundRemovalService(paths.models / "isnet-anime")
    app = FastAPI(title="Speech Bubble Comic Editor App", docs_url=None, redoc_url=None)
    app.state.desktop_launch_token = token
    app.state.background_removal = background_removal
    register_routes(app)

    @app.middleware("http")
    async def protect_desktop_api(request: Request, call_next):
        protected = request.url.path.startswith(("/desktop/", "/speech_bubble", "/speech-bubble-editor/"))
        is_static = request.url.path.startswith("/speech-bubble-editor/static/")
        if protected and not is_static:
            supplied = request.headers.get("X-SBE-Token", "") or request.query_params.get("token", "")
            if not secrets.compare_digest(str(supplied), token):
                return JSONResponse(status_code=403, content={"detail": "Invalid desktop launch token"})
        return await call_next(request)

    def require_token(request: Request, header_token: str = "") -> None:
        supplied = header_token or request.query_params.get("token", "")
        if not secrets.compare_digest(str(supplied), token):
            raise HTTPException(status_code=403, detail="Invalid desktop launch token")

    @app.get("/", include_in_schema=False)
    async def editor():
        configured = settings.load()
        query = urlencode(
            {
                "host": "desktop",
                "comic": "1",
                "token": token,
                "apiBase": "/speech_bubble",
                "forgeApiBase": "/speech-bubble-editor",
                "exportTransport": "multipart_canvas_v1",
                "autoSave": "1" if configured.get("auto_save", True) else "0",
                "autoSaveDelay": str(
                    int(configured.get("auto_save_interval_seconds", 30)) * 1000
                ),
                "startupBehavior": configured.get("startup_behavior", "ask"),
                "showEmptyCanvasGuide": "1" if configured.get("show_empty_canvas_guide", False) else "0",
                "sharedProjectImages": "1" if configured.get("shared_project_images", True) else "0",
                "theme": configured.get("theme", "system"),
                "language": configured.get("language", "auto"),
            }
        )
        return RedirectResponse(f"/speech-bubble-editor/static/speech-bubble-editor.html?{query}")

    @app.get("/desktop/health")
    async def health(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        return {"ok": True, "host": "desktop"}

    @app.get("/desktop/background-removal/model")
    async def background_removal_model_status(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        return background_removal.status()

    @app.post("/desktop/background-removal/model/download")
    async def background_removal_model_download(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        return background_removal.start_download()

    @app.post("/desktop/background-removal/model/cancel")
    async def background_removal_model_cancel(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        return background_removal.cancel_download()

    @app.delete("/desktop/background-removal/model")
    async def background_removal_model_delete(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        try:
            return background_removal.remove_model()
        except RuntimeError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/desktop/background-removal/infer")
    async def background_removal_infer(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        content_length = int(request.headers.get("content-length") or 0)
        if content_length > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="画像サイズが大きすぎます。")
        raw = await request.body()
        try:
            mask, width, height = await asyncio.to_thread(background_removal.infer_mask, raw)
        except FileNotFoundError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except (RuntimeError, ValueError, OSError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return Response(
            content=mask,
            media_type="image/png",
            headers={"X-SBE-Image-Width": str(width), "X-SBE-Image-Height": str(height)},
        )

    @app.get("/desktop/config")
    async def config(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        return {"ok": True, "settings": settings.load()}

    @app.put("/desktop/config")
    async def update_config(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        payload = await request.json()
        return {"ok": True, "settings": settings.save(payload if isinstance(payload, dict) else {})}

    @app.post("/desktop/export-directory/validate")
    async def validate_export_directory(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        payload = await request.json()
        raw = str(payload.get("path", "") or "").strip()
        path = Path(raw).expanduser()
        if not raw or not path.is_absolute():
            raise HTTPException(status_code=400, detail="出力フォルダーは絶対パスで指定してください。")
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise HTTPException(status_code=400, detail="出力フォルダーが存在しません。") from error
        if not resolved.is_dir():
            raise HTTPException(status_code=400, detail="出力先はフォルダーを指定してください。")
        if not os.access(resolved, os.W_OK):
            raise HTTPException(status_code=400, detail="出力フォルダーへ書き込めません。")
        return {"ok": True, "path": str(resolved)}

    def cache_files() -> list[Path]:
        files: list[Path] = []
        for root in (paths.recovery, paths.temp):
            if root.is_dir():
                files.extend(path for path in root.rglob("*") if path.is_file())
        return files

    @app.get("/desktop/cache/status")
    async def cache_status(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        recovery_files = [path for path in paths.recovery.rglob("*") if path.is_file()]
        temporary_files = [path for path in paths.temp.rglob("*") if path.is_file()]
        size = sum(path.stat().st_size for path in [*recovery_files, *temporary_files])
        recovery_status = recovery.status()
        return {
            "ok": True,
            "draft_files": len(recovery_files),
            "temporary_files": len(temporary_files),
            "total_size": size,
            "total_size_label": f"{size / (1024 * 1024):.1f} MB",
            "recovery": recovery_status,
        }

    @app.post("/desktop/cache/clear")
    async def clear_cache(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        removed = recovery.clear()
        for path in [path for path in paths.temp.rglob("*") if path.is_file()]:
            try:
                path.unlink()
                removed += 1
            except FileNotFoundError:
                continue
        return {"ok": True, "removed": removed}

    @app.post("/desktop/recovery/save")
    async def save_recovery(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        payload = await request.json()
        try:
            return recovery.save(
                payload if isinstance(payload, dict) else {},
                checkpoint=bool(payload.get("checkpoint")) if isinstance(payload, dict) else False,
            )
        except (OSError, ValueError, TypeError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/desktop/recovery/load")
    async def load_recovery(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        return recovery.load()

    @app.get("/desktop/recovery/status")
    async def recovery_status(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        return {"ok": True, **recovery.status()}

    @app.get("/desktop/recent")
    async def get_recent(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        return {"ok": True, "items": recent.load()}

    @app.post("/desktop/recent/remove")
    async def remove_recent(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        payload = await request.json()
        return {"ok": True, "items": recent.remove(str(payload.get("path", "")))}

    @app.post("/desktop/project/save")
    async def save_project(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        payload = await request.json()
        requested = Path(str(payload.pop("path", "")))
        if not requested.is_absolute():
            raise HTTPException(status_code=400, detail="A native-selected absolute project path is required")
        try:
            result = projects.save(requested, payload)
            recent.touch(Path(result["path"]))
            return result
        except (OSError, ValueError, TypeError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/desktop/project/open")
    async def open_project(request: Request, x_sbe_token: str = Header(default="")):
        require_token(request, x_sbe_token)
        payload = await request.json()
        requested = Path(str(payload.get("path", "")))
        if not requested.is_absolute():
            raise HTTPException(status_code=400, detail="A native-selected absolute project path is required")
        try:
            result = projects.load(requested)
            recent.touch(requested)
            return result
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    return app
