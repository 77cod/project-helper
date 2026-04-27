from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.core.config import Settings


def build_chat_model(settings: Settings) -> ChatOpenAI | None:
    if not settings.deepseek_api_key:
        return None

    return ChatOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=f"{settings.deepseek_base_url}/v1",
        model=settings.deepseek_model,
        temperature=0.2,
        streaming=True,
    )
