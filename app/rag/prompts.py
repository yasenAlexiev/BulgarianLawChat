SYSTEM_PROMPT = """Ти си асистент за българско законодателство.

Правила:
- Отговаряй САМО на базата на предоставените източници.
- Винаги цитирай релевантните членове (напр. чл. 344 от Кодекса на труда).
- Ако източниците не съдържат достатъчно информация, кажи това ясно.
- Не измисляй законови норми.
- Пиши на български, ясно и структурирано.
- Това е информационна помощ, не юридическа консултация."""

USER_PROMPT_TEMPLATE = """Въпрос:
{question}

Източници:
{context}

Дай отговор на въпроса, като цитираш само горните източници."""


def format_context_block(
    index: int,
    law: str,
    article: str,
    paragraph: str | None,
    text: str,
) -> str:
    cite = article
    if paragraph:
        cite = f"{article}, {paragraph}"
    return f"[{index}] {law} — {cite}\n{text}"


def build_user_prompt(question: str, chunks: list) -> str:
    blocks = [
        format_context_block(
            i,
            chunk.law,
            chunk.article,
            chunk.paragraph,
            chunk.text,
        )
        for i, chunk in enumerate(chunks, start=1)
    ]
    context = "\n\n".join(blocks) if blocks else "(няма намерени източници)"
    return USER_PROMPT_TEMPLATE.format(question=question, context=context)
