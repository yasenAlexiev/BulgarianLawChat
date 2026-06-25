from __future__ import annotations

from app.config import get_settings
from app.rag.prompts import SYSTEM_PROMPT, build_user_prompt
from app.rag.retriever import SearchResult


def generate_answer(question: str, chunks: list[SearchResult]) -> str:
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
