from __future__ import annotations

import argparse
import ctypes
import json
import logging
import secrets
import sys
import threading
import webbrowser

from .paths import DesktopPaths, resource_root
from .runtime import ServerRuntime, free_loopback_port
from .server import create_app

_INSTANCE_MUTEX = None
_ACTIVATE_EVENT = None
APP_NAME = "Speech Bubble Comic Editor App"
_INSTANCE_MUTEX_NAME = "Local\\SpeechBubbleComicEditorApp"
_ACTIVATE_EVENT_NAME = "Local\\SpeechBubbleComicEditorApp.Activate"


def enable_windows_high_dpi() -> None:
    """Use Windows per-monitor DPI scaling without applying a second UI zoom."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


def acquire_single_instance() -> bool:
    global _INSTANCE_MUTEX, _ACTIVATE_EVENT
    if sys.platform != "win32":
        return True
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, _INSTANCE_MUTEX_NAME)
    if not handle:
        return True
    if kernel32.GetLastError() == 183:
        kernel32.CloseHandle(handle)
        event = kernel32.OpenEventW(0x0002, False, _ACTIVATE_EVENT_NAME)
        if event:
            kernel32.SetEvent(event)
            kernel32.CloseHandle(event)
        return False
    _INSTANCE_MUTEX = handle
    _ACTIVATE_EVENT = kernel32.CreateEventW(None, False, False, _ACTIVATE_EVENT_NAME)
    return True


def release_single_instance() -> None:
    global _INSTANCE_MUTEX, _ACTIVATE_EVENT
    if sys.platform != "win32":
        return
    kernel32 = ctypes.windll.kernel32
    for name in ("_ACTIVATE_EVENT", "_INSTANCE_MUTEX"):
        handle = globals().get(name)
        if handle:
            kernel32.CloseHandle(handle)
            globals()[name] = None


def _work_areas() -> list[tuple[int, int, int, int]]:
    if sys.platform != "win32":
        return []
    user32 = ctypes.windll.user32
    class Rect(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    class MonitorInfo(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", Rect), ("rcWork", Rect), ("dwFlags", ctypes.c_ulong)]
    areas: list[tuple[int, int, int, int]] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(Rect), ctypes.c_long)

    def callback(monitor, _dc, _rect, _data):
        info = MonitorInfo()
        info.cbSize = ctypes.sizeof(MonitorInfo)
        if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            work = info.rcWork
            areas.append((int(work.left), int(work.top), int(work.right), int(work.bottom)))
        return 1

    try:
        user32.EnumDisplayMonitors(None, None, callback_type(callback), 0)
    except (AttributeError, OSError):
        areas = []
    if areas:
        return areas
    try:
        rect = Rect()
        if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return [(int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))]
    except (AttributeError, OSError):
        pass
    return []


def normalized_window_geometry(settings: dict) -> dict:
    settings = settings if isinstance(settings, dict) else {}
    try:
        width = int(settings.get("window_width", 1440))
    except (TypeError, ValueError):
        width = 1440
    try:
        height = int(settings.get("window_height", 900))
    except (TypeError, ValueError):
        height = 900
    width = max(900, min(3840, width))
    height = max(640, min(2160, height))
    maximized_value = settings.get("window_maximized", True)
    if isinstance(maximized_value, str):
        maximized = maximized_value.strip().lower() not in {"", "0", "false", "no", "off"}
    else:
        maximized = bool(maximized_value)
    areas = _work_areas()
    if not areas:
        return {"width": width, "height": height, "x": None, "y": None, "maximized": maximized}
    left = settings.get("window_left")
    top = settings.get("window_top")
    try:
        left = int(left) if left is not None else None
        top = int(top) if top is not None else None
    except (TypeError, ValueError):
        left = top = None
    area = next((candidate for candidate in areas if left is not None and top is not None and candidate[0] <= left < candidate[2] and candidate[1] <= top < candidate[3]), areas[0])
    area_left, area_top, area_right, area_bottom = area
    width = min(width, max(900, area_right - area_left))
    height = min(height, max(640, area_bottom - area_top))
    if left is None or top is None:
        left = area_left + max(0, (area_right - area_left - width) // 2)
        top = area_top + max(0, (area_bottom - area_top - height) // 2)
    else:
        left = max(area_left, min(area_right - width, left))
        top = max(area_top, min(area_bottom - height, top))
    return {"width": width, "height": height, "x": left, "y": top, "maximized": maximized}


class DesktopBridge:
    def __init__(
        self,
        initial_directory: str = "",
        export_directory: str = "",
        app_url: str = "",
        settings_store=None,
    ):
        # Native window objects must remain private. pywebview reflects public
        # bridge attributes into JavaScript; exposing WinForms/WebView2 objects
        # here makes that reflection recurse through the native object graph.
        self._window = None
        self._palette_window = None
        self._native_icon = None
        self._webview = None
        self.app_url = app_url
        self.initial_directory = initial_directory
        self.export_directory = export_directory
        self.open_dialog = 10
        self.folder_dialog = 20
        self.save_dialog = 30
        self._palette_closing = False
        self._settings_store = settings_store
        self._close_approved = False
        self._close_in_progress = False
        self._window_state_tracking = False

    @staticmethod
    def _first_path(value) -> str:
        if isinstance(value, (list, tuple)):
            return str(value[0]) if value else ""
        return str(value or "")

    def choose_project_save(self) -> str:
        if not self._window:
            return ""
        result = self._window.create_file_dialog(
            self.save_dialog,
            directory=self.initial_directory or "",
            save_filename="speech-bubble-4koma-project.sbeproj",
            file_types=("Speech Bubble Comic Editor App Project (*.sbeproj)",),
        )
        return self._first_path(result)

    def choose_project_open(self) -> str:
        if not self._window:
            return ""
        result = self._window.create_file_dialog(
            self.open_dialog,
            directory=self.initial_directory or "",
            allow_multiple=False,
            file_types=("Speech Bubble Comic Editor App Project (*.sbeproj)",),
        )
        return self._first_path(result)

    def choose_export_directory(self, initial_directory: str = "") -> str:
        if not self._window:
            return ""
        directory = str(initial_directory or self.export_directory or self.initial_directory or "")
        result = self._window.create_file_dialog(
            self.folder_dialog,
            directory=directory,
            allow_multiple=False,
        )
        selected = self._first_path(result)
        if selected:
            self.export_directory = selected
        return selected

    def _read_window_state(self) -> dict:
        window = self._window
        if not window:
            return {}
        state = {}
        for key in ("width", "height", "x", "y"):
            try:
                value = getattr(window, key)
                if value is not None:
                    state[f"window_{'left' if key == 'x' else 'top' if key == 'y' else key}"] = int(value)
            except (AttributeError, TypeError, ValueError):
                continue
        try:
            state["window_maximized"] = bool(getattr(window, "maximized"))
        except (AttributeError, TypeError, ValueError):
            pass
        return state

    def save_window_state(self, state=None) -> bool:
        if not self._settings_store:
            return False
        patch = state if isinstance(state, dict) else self._read_window_state()
        allowed = {"window_width", "window_height", "window_left", "window_top", "window_maximized"}
        patch = {key: value for key, value in patch.items() if key in allowed}
        if not patch:
            return False
        try:
            self._settings_store.save(patch)
            return True
        except (OSError, TypeError, ValueError):
            logging.exception("Could not save native window state")
            return False

    def _restore_window(self) -> bool:
        window = self._window
        if not window:
            return False
        geometry = normalized_window_geometry(self._settings_store.load() if self._settings_store else {})
        try:
            if geometry["x"] is not None and geometry["y"] is not None:
                window.move(geometry["x"], geometry["y"])
            window.resize(geometry["width"], geometry["height"])
            if geometry["maximized"]:
                maximize = getattr(window, "maximize", None)
                if callable(maximize):
                    maximize()
            else:
                restore = getattr(window, "restore", None)
                if callable(restore):
                    restore()
            show = getattr(window, "show", None)
            if callable(show):
                show()
            for method_name in ("bring_to_front", "focus"):
                method = getattr(window, method_name, None)
                if callable(method):
                    method()
            return True
        except Exception:
            logging.exception("Could not restore the native editor window")
            return False

    def _activate_listener(self) -> None:
        if sys.platform != "win32" or not _ACTIVATE_EVENT:
            return
        try:
            kernel32 = ctypes.windll.kernel32
            while _ACTIVATE_EVENT:
                result = kernel32.WaitForSingleObject(_ACTIVATE_EVENT, 0xFFFFFFFF)
                if result != 0:
                    break
                self._restore_window()
        except (AttributeError, OSError):
            logging.exception("Could not listen for second-launch activation")

    def start_activation_listener(self) -> None:
        if sys.platform == "win32" and _ACTIVATE_EVENT:
            threading.Thread(target=self._activate_listener, name="sbe-activate", daemon=True).start()

    def _native_close_error(self, message: str) -> None:
        logging.error("Native close was not completed: %s", message)
        if sys.platform == "win32":
            try:
                ctypes.windll.user32.MessageBoxW(None, str(message), APP_NAME, 0x10)
            except (AttributeError, OSError):
                pass

    def _request_native_close(self) -> None:
        try:
            if not self._window:
                raise RuntimeError("Editor window is not available")
            self._window.evaluate_js(
                "window.SpeechBubbleDesktopEditor?.prepareNativeClose?.({fromNative:true});"
            )
        except Exception as error:
            self._close_in_progress = False
            self._native_close_error(str(error))

    def handle_closing(self, *_args) -> bool:
        if self._close_approved:
            return True
        if self._close_in_progress:
            return False
        self._close_in_progress = True
        self._run_async(self._request_native_close)
        return False

    def native_close_ready(self, ok=True, message="", cancelled=False) -> bool:
        self._close_in_progress = False
        if bool(cancelled):
            return False
        if not bool(ok):
            self._native_close_error(str(message or "終了前の保存に失敗しました。"))
            return False
        self.save_window_state()
        self._close_approved = True
        def destroy_after_api_response():
            try:
                if self._window:
                    self._window.destroy()
            except Exception as error:
                self._close_approved = False
                self._native_close_error(str(error))

        threading.Timer(0.05, destroy_after_api_response).start()
        return True

    def _bind_window_events(self, window) -> None:
        events = getattr(window, "events", None)
        if not events:
            return
        closing = getattr(events, "closing", None)
        if closing is not None:
            closing += self.handle_closing
        shown = getattr(events, "shown", None)
        if shown is not None:
            shown += self._configure_native_icon
            shown += self._enable_window_state_tracking
        for name in ("resized", "moved", "maximized", "restored"):
            event = getattr(events, name, None)
            if event is not None:
                event += lambda *_args: self._save_window_state_if_ready()

    def _configure_native_icon(self, *_args) -> None:
        """Apply the bundled koma mark to the Windows title bar and taskbar."""
        if sys.platform != "win32" or not self._window:
            return
        icon_path = resource_root() / "web" / "assets" / "speech-bubble-comic-editor-app.ico"
        if not icon_path.is_file():
            logging.warning("Application icon is missing: %s", icon_path)
            return
        try:
            import clr

            clr.AddReference("System.Drawing")
            from System import Action
            from System.Drawing import Icon

            native = getattr(self._window, "native", None)
            if native is None:
                return

            def configure():
                self._native_icon = Icon(str(icon_path))
                native.Icon = self._native_icon
                if hasattr(native, "ShowIcon"):
                    native.ShowIcon = True

            if getattr(native, "InvokeRequired", False):
                native.Invoke(Action(configure))
            else:
                configure()
        except Exception:
            logging.exception("Could not apply the application icon")

    def _enable_window_state_tracking(self, *_args) -> None:
        self._window_state_tracking = True
        self.save_window_state()

    def _save_window_state_if_ready(self) -> None:
        if self._window_state_tracking:
            self.save_window_state()

    @staticmethod
    def _run_async(callback) -> None:
        threading.Thread(target=callback, daemon=True).start()

    @staticmethod
    def _safe_geometry(value) -> dict:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError):
                value = {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _apply_snapshot(window, snapshot: str) -> None:
        if not window or not snapshot:
            return
        window.evaluate_js(
            "window.SpeechBubblePaletteSync?.apply("
            + json.dumps(str(snapshot), ensure_ascii=False)
            + ")"
        )

    def _forward_snapshot(self, source, target) -> None:
        def forward():
            try:
                snapshot = source.evaluate_js(
                    "window.SpeechBubblePaletteSync?.snapshot?.() || ''"
                )
                self._apply_snapshot(target, snapshot)
            except Exception:
                logging.exception("Could not synchronize the external palette")

        self._run_async(forward)

    def palette_ready(self) -> bool:
        if not self._window or not self._palette_window:
            return False
        self._forward_snapshot(self._window, self._palette_window)
        return True

    def palette_update(self, snapshot: str) -> bool:
        if not self._window:
            return False
        self._run_async(lambda: self._apply_snapshot(self._window, snapshot))
        return True

    def main_update(self, snapshot: str) -> bool:
        if not self._palette_window:
            return False
        self._run_async(lambda: self._apply_snapshot(self._palette_window, snapshot))
        return True

    def _configure_palette_native(self) -> None:
        if sys.platform != "win32" or not self._palette_window:
            return
        try:
            from System import Action
            from System.Windows.Forms import FormBorderStyle

            native = self._palette_window.native

            def configure():
                native.ShowInTaskbar = False
                native.FormBorderStyle = FormBorderStyle.SizableToolWindow
                native.MinimizeBox = False
                native.MaximizeBox = False
                if self._window and getattr(self._window, "native", None):
                    native.Owner = self._window.native

            if native.InvokeRequired:
                native.Invoke(Action(configure))
            else:
                configure()
        except Exception:
            logging.exception("Could not configure the native tool palette")

    def _palette_closed(self) -> None:
        self._palette_window = None
        self._palette_closing = False

    def open_palette(self, geometry=None) -> bool:
        if not self._webview or not self.app_url:
            return False
        requested = self._safe_geometry(geometry)
        width = max(580, min(960, int(requested.get("width") or 680)))
        height = max(420, min(1120, int(requested.get("height") or 720)))
        try:
            x = int(requested["x"]) if requested.get("x") is not None else None
            y = int(requested["y"]) if requested.get("y") is not None else None
        except (TypeError, ValueError):
            x = y = None
        if self._palette_window:
            try:
                self._palette_window.show()
                if x is not None and y is not None:
                    self._palette_window.move(x, y)
                self._palette_window.resize(width, height)
                return True
            except Exception:
                logging.exception("Could not reuse the external palette window")
                self._palette_window = None
        separator = "&" if "?" in self.app_url else "?"
        palette = self._webview.create_window(
            f"{APP_NAME} - Properties / Layers",
            url=f"{self.app_url}{separator}palette=1",
            js_api=self,
            width=width,
            height=height,
            x=x,
            y=y,
            min_size=(580, 420),
            resizable=True,
            on_top=False,
        )
        if not palette:
            return False
        self._palette_window = palette
        palette.events.shown += self._configure_palette_native
        palette.events.closed += self._palette_closed
        return True

    def close_palette(self) -> bool:
        palette = self._palette_window
        if not palette or self._palette_closing:
            return False
        self._palette_closing = True
        try:
            palette.destroy()
            return True
        except Exception:
            self._palette_closing = False
            logging.exception("Could not close the external palette window")
            return False

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--portable", action="store_true", help="Store application data beside the app")
    parser.add_argument("--browser", action="store_true", help="Development fallback: open in the default browser")
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    paths = DesktopPaths.create(portable=args.portable)
    log_path = paths.logs / "desktop-startup.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )
    enable_windows_high_dpi()
    if not acquire_single_instance():
        logging.info("A second launch was ignored because the Desktop app is already running")
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(
                None,
                f"{APP_NAME} はすでに起動しています。",
                APP_NAME,
                0x40,
            )
        return 0
    from .settings_store import SettingsStore

    settings_store = SettingsStore(paths.settings)
    settings = settings_store.load()
    token = secrets.token_urlsafe(32)
    port = free_loopback_port()
    runtime = ServerRuntime(create_app(paths, token), port)
    runtime.start()
    url = f"http://127.0.0.1:{port}/"
    logging.info("Desktop server ready at %s", url)
    try:
        if args.browser:
            webbrowser.open(url)
            input(f"{APP_NAME} is running. Press Enter to stop.\n")
            return 0
        try:
            import webview
        except ImportError as error:
            raise RuntimeError(
                "pywebview is required for the desktop window. "
                "Install requirements-desktop.txt or use --browser for development."
            ) from error
        geometry = normalized_window_geometry(settings)
        bridge = DesktopBridge(
            settings.get("last_project_directory", ""),
            settings.get("last_export_directory", "") or settings.get("export_directory", ""),
            url,
            settings_store,
        )
        bridge._webview = webview
        bridge.open_dialog = webview.OPEN_DIALOG
        bridge.folder_dialog = webview.FOLDER_DIALOG
        bridge.save_dialog = webview.SAVE_DIALOG
        window = webview.create_window(
            APP_NAME,
            url=url,
            js_api=bridge,
            width=geometry["width"],
            height=geometry["height"],
            x=geometry["x"],
            y=geometry["y"],
            min_size=(900, 640),
            maximized=geometry["maximized"],
        )
        bridge._window = window
        bridge._bind_window_events(window)
        bridge.start_activation_listener()
        # Force the WebView2 renderer on Windows. Letting pywebview auto-select
        # a legacy renderer can produce an unusable window on some machines.
        logging.info("Starting pywebview with the Edge Chromium renderer")
        webview.start(
            debug=False,
            gui="edgechromium",
            private_mode=False,
            storage_path=str(paths.root / "webview"),
        )
        return 0
    except Exception:
        logging.exception("%s failed to start", APP_NAME)
        raise
    finally:
        runtime.stop()
        release_single_instance()


if __name__ == "__main__":
    raise SystemExit(run())
