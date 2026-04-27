from __future__ import annotations

import asyncio
import json
from pathlib import Path
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.project_report_builder import build_project_report
from app.core.config import Settings
from app.models import AnalysisRun, ChatMessage, ChatSession, Project
from app.services.codebase_tools import CodebaseTools
from app.services.event_bus import EventBus
from app.services.llm_client import build_chat_model
from app.services.repo_manager import RepoManager
from app.services.repo_url import normalize_github_url, project_slug


class ProjectAnalysisService:
    def __init__(self, settings: Settings, event_bus: EventBus) -> None:
        self.settings = settings
        self.event_bus = event_bus
        self.repo_manager = RepoManager(settings)
        self.chat_model = build_chat_model(settings)

    async def create_or_reuse_analysis(self, session: AsyncSession, repo_url: str) -> tuple[Project, AnalysisRun, bool]:
        normalized = normalize_github_url(repo_url)
        existing = await session.scalar(select(Project).where(Project.repo_url == normalized))
        if existing and existing.report_json:
            cached_run = await session.scalar(
                select(AnalysisRun)
                .where(AnalysisRun.project_id == existing.id)
                .order_by(AnalysisRun.id.desc())
            )
            return existing, cached_run, True

        if existing is None:
            existing = Project(
                repo_url=normalized,
                slug=project_slug(normalized),
                name=normalized.rsplit("/", 1)[-1],
                status="queued",
            )
            session.add(existing)
            await session.flush()

        run = AnalysisRun(project_id=existing.id, status="queued", progress=0, current_step="queued")
        session.add(run)
        await session.commit()
        await session.refresh(existing)
        await session.refresh(run)
        return existing, run, False

    async def run_analysis(self, session: AsyncSession, project_id: int, run_id: int) -> None:
        project = await session.get(Project, project_id)
        run = await session.get(AnalysisRun, run_id)
        if project is None or run is None:
            return

        try:
            await self._update_run(session, project, run, "running", 10, "正在克隆仓库")
            repo_path = self.repo_manager.prepare_repo(project.repo_url)
            project.local_path = str(repo_path)

            await self._maybe_wait()
            await self._update_run(session, project, run, "running", 55, "正在分析目录和技术栈")
            report = build_project_report(repo_path, project.repo_url)

            await self._maybe_wait()
            await self._update_run(session, project, run, "running", 85, "正在整理小白友好解读")
            project.report_json = json.dumps(report, ensure_ascii=False)

            await self._maybe_wait()
            run.status = "completed"
            run.progress = 100
            run.current_step = "分析完成"
            project.status = "completed"
            await session.commit()
            await self.event_bus.publish(
                f"analysis:{run.id}",
                {"status": run.status, "progress": run.progress, "step": run.current_step},
            )
        except Exception as exc:  # pragma: no cover
            run.status = "failed"
            run.error_message = str(exc)
            project.status = "failed"
            await session.commit()
            await self.event_bus.publish(
                f"analysis:{run.id}",
                {"status": "failed", "progress": run.progress, "step": str(exc)},
            )
            raise

    async def list_projects(self, session: AsyncSession) -> list[Project]:
        result = await session.scalars(select(Project).order_by(Project.id.desc()))
        return list(result)

    async def get_report(self, session: AsyncSession, project_id: int) -> dict | None:
        project = await session.get(Project, project_id)
        if project is None or not project.report_json:
            return None
        return json.loads(project.report_json)

    async def create_chat_session(self, session: AsyncSession, project_id: int, title: str) -> ChatSession:
        chat = ChatSession(project_id=project_id, title=title)
        session.add(chat)
        await session.commit()
        await session.refresh(chat)
        return chat

    async def answer_question(self, session: AsyncSession, session_id: int, question: str) -> dict:
        chunks: list[str] = []
        references: list[dict] = []
        async for event in self.answer_question_stream(session, session_id, question):
            if event["type"] == "meta":
                references = event["references"]
            elif event["type"] == "chunk":
                chunks.append(event["content"])
        return {"answer": "".join(chunks), "references": references}

    async def answer_question_stream(
        self,
        session: AsyncSession,
        session_id: int,
        question: str,
    ) -> AsyncIterator[dict]:
        chat_session = await session.get(ChatSession, session_id)
        if chat_session is None:
            raise ValueError("Chat session not found.")

        project = await session.get(Project, chat_session.project_id)
        if project is None or not project.local_path:
            raise ValueError("Project is not ready for question answering.")

        project_path = Path(project.local_path)
        tools = CodebaseTools(project_path)
        references = tools.search_code(question)
        file_list = tools.list_files(limit=8)
        context_blocks = [
            f"文件列表：{', '.join(file_list)}",
            *[f"{item['path']}:\n{tools.read_file(item['path'])}" for item in references],
        ]
        answer = await self._generate_answer(question, context_blocks, references)

        session.add(ChatMessage(session_id=session_id, role="user", content=question))
        session.add(
            ChatMessage(
                session_id=session_id,
                role="assistant",
                content=answer,
                references_json=json.dumps(references, ensure_ascii=False),
            )
        )
        await session.commit()
        yield {"type": "meta", "references": references}
        for chunk in self._chunk_text(answer):
            yield {"type": "chunk", "content": chunk}
        yield {"type": "done"}

    async def _update_run(
        self,
        session: AsyncSession,
        project: Project,
        run: AnalysisRun,
        status: str,
        progress: int,
        step: str,
    ) -> None:
        run.status = status
        run.progress = progress
        run.current_step = step
        project.status = status
        await session.commit()
        await self.event_bus.publish(
            f"analysis:{run.id}",
            {"status": status, "progress": progress, "step": step},
        )

    async def _maybe_wait(self) -> None:
        if self.settings.analysis_delay_ms > 0:
            await asyncio.sleep(self.settings.analysis_delay_ms / 1000)

    async def _generate_answer(self, question: str, context_blocks: list[str], references: list[dict]) -> str:
        if self.chat_model is None:
            if not references:
                return (
                    f"我暂时没有在源码里直接搜到和“{question}”完全对应的内容。"
                    " 建议先从 README、入口文件和 service / api 相关目录开始追踪。"
                )
            summary = "，".join(item["path"] for item in references)
            snippets = "\n\n".join(context_blocks[1:])
            return (
                f"我先用搜索代码工具帮你定位到了这些文件：{summary}。\n\n"
                "用小白能懂的话说，它们就是最可能藏着答案的地方。下面是我找到的关键片段：\n\n"
                f"{snippets}"
            )

        context_text = "\n\n".join(context_blocks)
        prompt = (
            "你是项目学习助手，要用非常通俗的中文回答源码问题。"
            " 先明确答案，再引用文件路径，不要编造不存在的内容。\n\n"
            f"用户问题：{question}\n\n"
            f"代码上下文：\n{context_text}"
        )
        response = await self.chat_model.ainvoke(prompt)
        return response.content if isinstance(response.content, str) else str(response.content)

    def _chunk_text(self, text: str, chunk_size: int = 80) -> list[str]:
        return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)] or [""]
