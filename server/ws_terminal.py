"""WebSocket <-> PTY bridge for the workspace terminal.

One sandboxed zsh per socket. Output is read from the pty master on the event
loop (add_reader) and forwarded as text frames; incoming text frames are
written to the pty; a JSON frame {"type":"resize"} resizes it."""

from __future__ import annotations

import asyncio
import codecs
import json
import os
import threading

from fastapi import WebSocket, WebSocketDisconnect

from engine import workspace
from engine.sandbox import ShellProcess


class TerminalRegistry:
    """Live shells by run id, so a reset can kill the shell of the run it retires."""

    def __init__(self) -> None:
        self._shells: dict[str, set[ShellProcess]] = {}
        self._lock = threading.Lock()

    def add(self, run_id: str, shell: ShellProcess) -> None:
        with self._lock:
            self._shells.setdefault(run_id, set()).add(shell)

    def remove(self, run_id: str, shell: ShellProcess) -> None:
        with self._lock:
            self._shells.get(run_id, set()).discard(shell)

    def kill(self, run_id: str) -> None:
        with self._lock:
            shells = self._shells.pop(run_id, set())
        for s in shells:
            s.kill()

    def kill_all(self) -> None:
        with self._lock:
            ids = list(self._shells)
        for run_id in ids:
            self.kill(run_id)


async def terminal_socket(websocket: WebSocket, run_id: str) -> None:
    state = websocket.app.state
    row = state.db.get_run(run_id)
    if row is None or row["status"] == "abandoned":
        await websocket.close(code=4004, reason="no such run")
        return
    ws_dir = workspace.workspace_path(run_id)
    if not ws_dir.exists():
        workspace.create(run_id, state.incidents[row["incident_id"]])

    await websocket.accept()
    shell = state.sandbox.spawn_shell(cwd=ws_dir)
    state.terminals.add(run_id, shell)
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    fd = shell.master_fd

    def on_readable() -> None:
        try:
            data = os.read(fd, 65536)
        except OSError:
            data = b""
        if not data:
            loop.remove_reader(fd)
            queue.put_nowait(None)
        else:
            queue.put_nowait(data)

    loop.add_reader(fd, on_readable)
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

    async def pump_out() -> None:
        while True:
            data = await queue.get()
            if data is None:
                try:
                    await websocket.send_text("\r\n[shell exited]\r\n")
                    await websocket.close()
                except Exception:
                    pass
                return
            await websocket.send_text(decoder.decode(data))

    out_task = asyncio.create_task(pump_out())
    state.db.add_event(run_id, "terminal_opened")
    try:
        while True:
            msg = await websocket.receive_text()
            if msg.startswith("{"):
                try:
                    obj = json.loads(msg)
                except json.JSONDecodeError:
                    obj = None
                if isinstance(obj, dict) and "type" in obj:
                    # control frame (resize, ping); never typed into the shell
                    if obj["type"] == "resize":
                        try:
                            shell.resize(int(obj.get("cols", 80)), int(obj.get("rows", 24)))
                        except (OSError, ValueError):
                            pass
                    continue
            try:
                os.write(fd, msg.encode())
            except OSError:
                break
    except WebSocketDisconnect:
        pass
    finally:
        try:
            loop.remove_reader(fd)
        except Exception:
            pass
        state.terminals.remove(run_id, shell)
        shell.kill()
        out_task.cancel()
