INSUFFICIENT_INFO_MESSAGE = (
    "Не намирам достатъчно информация в предоставените нормативни текстове."
)

SYSTEM_PROMPT = f"""Ти си помощник за търсене в български нормативни актове.

Правила:
- Отговаряй САМО на базата на предоставения контекст.
- Ако в контекста няма достатъчно информация за отговор на въпроса, отговори ТОЧНО с:
  "{INSUFFICIENT_INFO_MESSAGE}"
- Не давай правен съвет и не тълкувай като адвокат.
- Не измисляй закони, членове, алинеи, срокове, суми или изключения.
- Използвай само факти, които изрично присъстват в контекста.
- Винаги цитирай закона, члена и алинеята, когато са налични в контекста.
- Ако контекстът е неясен или противоречив, кажи това изрично.
- Отговорът трябва да бъде ясен, кратък и разбираем на български език."""

USER_PROMPT_TEMPLATE = """Въпрос:
{question}

Контекст:
{context}

Дай отговор на български език.
Цитирай използваните разпоредби (закон, член, алинея).
Ако контекстът не съдържа отговор, не предполагай — кажи, че няма достатъчно информация."""


def format_context_block(
    index: int,
    law: str,
    article: str,
    paragraph: str | None,
    text: str,
    metadata: dict | None = None,
) -> str:
    cite = article
    if paragraph:
        cite = f"{article}, {paragraph}"

    lines = [f"[{index}] {law} — {cite}"]
    source_url = (metadata or {}).get("source_url")
    if source_url:
        lines.append(f"Източник: {source_url}")
    lines.append(text)
    return "\n".join(lines)


def build_user_prompt(question: str, chunks: list) -> str:
    if not chunks:
        context = "(няма намерени нормативни текстове в базата)"
    else:
        blocks = [
            format_context_block(
                i,
                chunk.law,
                chunk.article,
                chunk.paragraph,
                chunk.text,
                chunk.metadata,
            )
            for i, chunk in enumerate(chunks, start=1)
        ]
        context = "\n\n".join(blocks)

    return USER_PROMPT_TEMPLATE.format(question=question, context=context)
