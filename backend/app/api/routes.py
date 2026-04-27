from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
import json

from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import AnalyzeRequest, AnalyzeResponse, ChatMessageCreate, ChatSessionCreate, ProjectSummary


def build_router() -> APIRouter:
    router = APIRouter(prefix="/api")

    async def get_session(request: Request):
        async for session in request.app.state.get_session():
            yield session

    @router.post("/projects/analyze", response_model=AnalyzeResponse)
    async def analyze_project(
        payload: AnalyzeRequest,
        request: Request,
        session: AsyncSession = Depends(get_session),
    ):
        service = request.app.state.analysis_service
        project, run, cached = await service.create_or_reuse_analysis(session, payload.repo_url)
        if cached:
            return AnalyzeResponse(project_id=project.id, run_id=run.id, status="completed", cached=True)

        if request.app.state.run_analysis_inline:
            await service.run_analysis(session, project.id, run.id)
            refreshed = await session.get(type(run), run.id)
            return JSONResponse(
                status_code=202,
                content=AnalyzeResponse(
                    project_id=project.id,
                    run_id=run.id,
                    status=refreshed.status,
                    cached=False,
                ).model_dump(),
            )

        request.app.state.spawn_task(project.id, run.id)
        return JSONResponse(
            status_code=202,
            content=AnalyzeResponse(
                project_id=project.id,
                run_id=run.id,
                status=run.status,
                cached=False,
            ).model_dump(),
        )

    @router.get("/projects", response_model=list[ProjectSummary])
    async def list_projects(
        request: Request,
        session: AsyncSession = Depends(get_session),
    ):
        projects = await request.app.state.analysis_service.list_projects(session)
        return [
            ProjectSummary(id=project.id, repo_url=project.repo_url, name=project.name, status=project.status)
            for project in projects
        ]

    @router.get("/projects/{project_id}/report")
    async def get_report(
        project_id: int,
        request: Request,
        session: AsyncSession = Depends(get_session),
    ):
        report = await request.app.state.analysis_service.get_report(session, project_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found.")
        return JSONResponse(report)

    @router.get("/runs/{run_id}/events")
    async def stream_events(run_id: int, request: Request):
        return StreamingResponse(
            request.app.state.event_bus.stream(f"analysis:{run_id}"),
            media_type="text/event-stream",
        )

    @router.post("/chat/sessions")
    async def create_chat_session(
        payload: ChatSessionCreate,
        request: Request,
        session: AsyncSession = Depends(get_session),
    ):
        chat = await request.app.state.analysis_service.create_chat_session(session, payload.project_id, payload.title)
        return {"id": chat.id, "project_id": chat.project_id, "title": chat.title}

    @router.post("/chat/sessions/{session_id}/messages")
    async def ask_question(
        session_id: int,
        payload: ChatMessageCreate,
        request: Request,
        session: AsyncSession = Depends(get_session),
    ):
        try:
            return await request.app.state.analysis_service.answer_question(session, session_id, payload.question)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/chat/sessions/{session_id}/messages/stream")
    async def ask_question_stream(
        session_id: int,
        payload: ChatMessageCreate,
        request: Request,
        session: AsyncSession = Depends(get_session),
    ):
        async def event_stream():
            try:
                async for event in request.app.state.analysis_service.answer_question_stream(
                    session, session_id, payload.question
                ):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except ValueError as exc:
                yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return router
