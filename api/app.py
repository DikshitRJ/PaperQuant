from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import VERSION
from .routes import (
    algorithms,
    health,
    logs,
    market,
    positions,
    session,
    settings,
    stats,
)
from .services.session_manager import SessionManager
from .websocket import ws_router


def create_app(session_manager: SessionManager | None = None) -> FastAPI:
    manager = session_manager or SessionManager()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await manager.initialize()
        yield
        await manager.shutdown()

    app = FastAPI(title="PaperQuant API", version=VERSION, lifespan=lifespan)
    app.state.session_manager = manager
    app.state.started_at = time.time()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["tauri://localhost", "http://localhost", "http://127.0.0.1"],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for route in (
        health,
        session,
        positions,
        stats,
        algorithms,
        settings,
        logs,
        market,
    ):
        app.include_router(route.router, prefix="/api")
    app.include_router(ws_router)
    return app
