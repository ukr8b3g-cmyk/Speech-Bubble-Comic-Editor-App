"""Single admitted conversion, with ownership retained after HTTP cancellation."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import uuid

log = logging.getLogger(__name__)

class BusyError(RuntimeError): pass
class UnavailableError(RuntimeError): pass

class MangaFinishService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='manga-finish')
        self.lease = None
        self.accepting = True

    def reserve(self):
        if not self.accepting: raise UnavailableError()
        try:
            from . import manga_finish
        except (ImportError, OSError) as exc:
            raise UnavailableError() from exc
        if self.lease is not None: raise BusyError()
        self.lease = uuid.uuid4().hex
        return self.lease

    def release(self, lease):
        if self.lease == lease: self.lease = None

    async def convert(self, lease, raw, settings):
        from .manga_finish import convert_image
        loop = asyncio.get_running_loop()
        try:
            future = self.executor.submit(convert_image, raw, settings)
        except BaseException:
            self.release(lease)
            raise
        def done(f):
            try:
                f.result()
            except Exception:
                log.exception('Manga Finish worker failed')
            try: loop.call_soon_threadsafe(self.release, lease)
            except RuntimeError: pass  # loop already stopped during process shutdown
        future.add_done_callback(done)
        wrapped = asyncio.wrap_future(future)
        wrapped.add_done_callback(lambda f: None if f.cancelled() else f.exception())
        return await asyncio.shield(wrapped)

    async def close(self):
        self.accepting = False
        await asyncio.to_thread(self.executor.shutdown, wait=True, cancel_futures=True)

def parse_settings(query):
    from .manga_finish import MangaFinishSettings, validate_settings
    from dataclasses import asdict
    allowed = asdict(MangaFinishSettings())
    raw = {}
    seen = set()
    for key, value in query.multi_items():
        if key in seen: raise ValueError('Duplicate query parameter')
        seen.add(key)
        if key == 'token': continue
        if key not in allowed: raise ValueError('Unknown setting')
        if key in ('halftone','white_lines'):
            if value not in ('true','false'): raise ValueError('Boolean must be true or false')
            raw[key] = value == 'true'
        else:
            raw[key] = int(value) if key == 'screen_lines' else float(value)
    return validate_settings(raw)

def register_manga_route(app, require_token):
    from fastapi import Request, Header
    from fastapi.responses import JSONResponse, Response
    from contextlib import asynccontextmanager
    service = MangaFinishService()
    app.state.manga_finish = service
    prior = app.router.lifespan_context
    @asynccontextmanager
    async def lifespan(app):
        async with prior(app):
            try: yield
            finally: await service.close()
    app.router.lifespan_context = lifespan

    @app.post('/desktop/comic-conversion/manga-finish')
    async def convert(request: Request, x_sbe_token: str = Header(default='')):
        require_token(request, x_sbe_token)
        english = request.headers.get('X-SBE-Language') == 'en'
        def error(status,code,ja,en):
            return JSONResponse({'detail':en if english else ja,'code':code},status_code=status,
                                headers={'Retry-After':'1'} if status == 429 else None)
        try:
            settings = parse_settings(request.query_params)
        except (ImportError, OSError):
            return error(503,'manga_finish_unavailable','漫画仕上げを読み込めません。','Manga Finish is unavailable.')
        except (ValueError,TypeError,OverflowError):
            return error(422,'invalid_settings','仕上げ設定が不正です。','Invalid finishing settings.')
        try: lease = service.reserve()
        except BusyError:
            return error(429,'manga_finish_busy','前の処理の終了を待って再実行してください。','Wait for the previous conversion and try again.')
        except UnavailableError:
            return error(503,'manga_finish_unavailable','漫画仕上げを利用できません。','Manga Finish is unavailable.')
        submitted = False
        from .manga_finish import MAX_BYTES, ImageTooLarge
        try:
            declared=request.headers.get("content-length")
            if declared is not None and int(declared)>MAX_BYTES: raise ImageTooLarge()
            body = bytearray()
            async with asyncio.timeout(30):
                async for chunk in request.stream():
                    if len(body)+len(chunk)>MAX_BYTES: raise ImageTooLarge()
                    body.extend(chunk)
            submitted = True
            result = await service.convert(lease,bytes(body),settings)
            return Response(result.png,media_type='image/png',headers={
                'Cache-Control':'no-store','X-SBE-Image-Width':str(result.width),
                'X-SBE-Image-Height':str(result.height),'X-SBE-Processing-Ms':str(round(result.elapsed_ms,2))})
        except ImageTooLarge:
            return error(413,'image_too_large','画像サイズが上限を超えています。','Image exceeds size limits.')
        except TimeoutError:
            return error(408,'input_timeout','画像の読み込みがタイムアウトしました。','Image upload timed out.')
        except (ValueError,OSError):
            return error(400,'invalid_image','画像を読み込めません。','Invalid or unsupported image.')
        except Exception:
            log.exception('Manga Finish request failed')
            return error(500,'conversion_failed','漫画仕上げに失敗しました。','Manga finishing failed.')
        finally:
            if not submitted: service.release(lease)
