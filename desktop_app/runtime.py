from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass

import uvicorn


def free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


@dataclass
class ServerRuntime:
    app: object
    port: int
    server: uvicorn.Server | None = None
    thread: threading.Thread | None = None

    def start(self) -> None:
        # A windowed PyInstaller build has no console streams. Uvicorn's
        # default formatter probes sys.stderr.isatty(), which crashes when
        # sys.stderr is None before the local server starts.
        config = uvicorn.Config(
            self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="warning",
            log_config=None,
            access_log=False,
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, name="SpeechBubbleDesktopServer", daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self.server.started:
                return
            if not self.thread.is_alive():
                break
            time.sleep(0.05)
        raise RuntimeError("Desktop server did not start")

    def stop(self) -> None:
        if self.server:
            self.server.should_exit = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
