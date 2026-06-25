from __future__ import annotations

from collections.abc import Generator

from app.config import get_settings
from app.rag.prompts import (
    INSUFFICIENT_INFO_MESSAGE,
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.rag.retriever import SearchResult


def generate_answer(question: str, chunks: list[SearchResult]) -> str:
    if not chunks:
        return INSUFFICIENT_INFO_MESSAGE

    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for answer generation")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(question, chunks)},
        ],
    )
    content = response.choices[0].message.content
    return content.strip() if content else ""


def generate_answer_stream(
    question: str, chunks: list[SearchResult]
) -> Generator[str, None, None]:
    """Generate answer with streaming, yielding tokens as they arrive."""
    if not chunks:
        yield INSUFFICIENT_INFO_MESSAGE
        return

    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for answer generation")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    stream = client.chat.completions.create(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(question, chunks)},
        ],
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
