from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    repo_url: str


class AnalyzeResponse(BaseModel):
    project_id: int
    run_id: int
    status: str
    cached: bool = False


class ProjectSummary(BaseModel):
    id: int
    repo_url: str
    name: str
    status: str


class ChatSessionCreate(BaseModel):
    project_id: int
    title: str = "新会话"


class ChatMessageCreate(BaseModel):
    question: str = Field(min_length=1)
