from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import build_router
from app.core.config import Settings
from app.db import Database
from app.models import Base
from app.services.analysis_service import ProjectAnalysisService
from app.services.event_bus import EventBus


def create_app(overrides: dict[str, Any] | None = None) -> FastAPI:
    settings = Settings.from_overrides(overrides)
    database = Database(settings.database_url)
    event_bus = EventBus()
    analysis_service = ProjectAnalysisService(settings, event_bus)
    background_tasks: set[asyncio.Task] = set()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield
        for task in list(background_tasks):
            task.cancel()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    async def get_session() -> AsyncSession:
        async for session in database.session():
            yield session

    def spawn_task(project_id: int, run_id: int) -> None:
        async def runner() -> None:
            async for session in database.session():
                await analysis_service.run_analysis(session, project_id, run_id)
                break

        task = asyncio.create_task(runner())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    app.state.settings = settings
    app.state.db = database
    app.state.event_bus = event_bus
    app.state.analysis_service = analysis_service
    app.state.get_session = get_session
    app.state.run_analysis_inline = bool(settings.testing_repo_map)
    app.state.spawn_task = spawn_task

    @app.get("/health")
    async def healthcheck():
        return {"status": "ok"}

    app.include_router(build_router())
    return app


app = create_app()
