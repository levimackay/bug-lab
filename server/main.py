"""FastAPI app factory. `uvicorn server.main:app --port 8000`."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from engine.incidents import load_all
from engine.sandbox import SeatbeltSandbox
from server import routes
from server.db import DB_PATH, Database
from server.ws_terminal import TerminalRegistry, terminal_socket

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "frontend" / "dist"


def create_app(db_path: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.incidents = load_all()
        app.state.sandbox = SeatbeltSandbox()  # raises if sandbox-exec is unavailable: no unsandboxed mode
        app.state.db = Database(db_path or Path(os.environ.get("BUGLAB_DB", DB_PATH)))
        app.state.terminals = TerminalRegistry()
        yield
        app.state.terminals.kill_all()
        app.state.db.close()

    app = FastAPI(title="Bug Lab", lifespan=lifespan)
    app.include_router(routes.router)

    @app.websocket("/api/runs/{run_id}/terminal")
    async def terminal(websocket: WebSocket, run_id: str):
        await terminal_socket(websocket, run_id)

    if DIST.exists():
        app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str):
            candidate = DIST / path
            if path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(DIST / "index.html")

    return app


app = create_app()
