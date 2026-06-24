import json
import re
import sys
from datetime import date
from pathlib import Path

ARTICLE_RE = re.compile(
    r"^(?P<label>Чл\.|§)\s*(?P<num>\d+[а-яА-Я]?)\.\s*(?P<body>.*)$",
    re.IGNORECASE,
)
ALINEA_START_RE = re.compile(r"^\((?P<num>\d+)\)\s*(?P<text>.*)$")
ALINEA_NOTE_LINE_RE = re.compile(
    r"^\(((?:Нова|Предишна)\s+)?Ал\.\s*(?P<nums>[\d,\s]+)"
    r"(?:\s+(?:отм|изм|нова|зал)\.?)?[^)]*-\s*ДВ[^)]*\)\s*(?P<body>.*)$",
    re.IGNORECASE,
)
AMENDMENT_ONLY_RE = re.compile(
    r"^\((?:Отм|Изм|Нов|Доп|Попр|Предишен|Предишна|Зал)\.?\s*-.*\)$",
    re.IGNORECASE,
)
INLINE_AMENDMENT_RE = re.compile(
    r"^\((?:Ал\.\s*\d+[^)]*|Отм|Изм|Нов|Доп)[^)]*-\s*ДВ[^)]*\)\s*",
    re.IGNORECASE,
)

NOISE_LINES = {
    "get adobe flash player",
    "in order to view this page you need adobe flash player 9 (or higher) equivalent support!",
}
NOISE_PREFIXES = (
    "препратки от статии",
    "релевантни актове от европейското законодателство",
    "директиви:",
    "новини",
    "спектър",
    "форум",
    "посети форума",
    "rss",
    "last spektar",
)
STOP_SECTION_MARKERS = (
    "релевантни актове от европейското законодателство",
    "новини",
)

DEFAULT_SOURCE_URL = "https://lex.bg/laws/ldoc/2121934337"
DEFAULT_INPUT = Path(__file__).parent / "закон-за-задължения-и-договори.txt"


def normalize_title(raw_title: str) -> str:
    title = " ".join(raw_title.split())
    if not title:
        return title
    return title[0].upper() + title[1:].lower()


def is_noise_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    lower = stripped.lower()
    if lower in NOISE_LINES:
        return True
    return any(lower.startswith(prefix) for prefix in NOISE_PREFIXES)


def is_section_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if ARTICLE_RE.match(stripped):
        return False
    if stripped.startswith("("):
        return False
    if re.match(r"^[А-ЯA-Z]\)\s", stripped):
        return True
    if re.match(r"^[IVXLC]+\.\s", stripped):
        return True
    if re.match(r"^\d+\.\s+[А-ЯA-Z]", stripped):
        return True
    if re.match(r"^Глава\s", stripped, re.IGNORECASE):
        return True
    if re.match(r"^[А-ЯA-Z][А-ЯA-Z\s\-–—/]{3,}$", stripped) and len(stripped) < 120:
        return True
    if stripped.startswith("Преходни") or stripped.startswith("Заключителни"):
        return True
    if stripped.startswith("КЪМ ЗАКОНА"):
        return True
    if re.match(r"^\(ОБН\.", stripped, re.IGNORECASE):
        return True
    return False


def is_amendment_only(text: str) -> bool:
    return bool(AMENDMENT_ONLY_RE.match(text.strip()))


def parse_alinea_numbers(raw: str) -> list[int]:
    return [int(n.strip()) for n in raw.split(",") if n.strip().isdigit()]


def strip_leading_amendments(text: str) -> str:
    while text:
        match = INLINE_AMENDMENT_RE.match(text)
        if not match:
            break
        text = text[match.end() :].lstrip()
    return text


def format_article_label(kind: str, number: str) -> str:
    prefix = "чл." if kind.lower().startswith("чл") else "§"
    return f"{prefix} {number.lower()}" if number[-1].isalpha() else f"{prefix} {number}"


def format_paragraph_label(number: int) -> str:
    return f"ал. {number}"


def parse_article_body(initial_body: str, continuation_lines: list[str]) -> list[dict]:
    paragraphs: list[dict] = []
    next_number = 1

    def add_paragraph(text: str, number: int | None = None) -> None:
        nonlocal next_number
        cleaned = text.strip()
        if not cleaned:
            return
        if number is None:
            number = next_number
            next_number += 1
        else:
            next_number = max(next_number, number + 1)
        paragraphs.append(
            {"paragraph": format_paragraph_label(number), "text": cleaned}
        )

    pending_body = initial_body.strip()
    if is_amendment_only(pending_body):
        add_paragraph(pending_body)
        pending_body = ""
    else:
        pending_body = strip_leading_amendments(pending_body)
        if pending_body:
            add_paragraph(pending_body)

    for line in continuation_lines:
        stripped = line.strip()
        if not stripped or is_noise_line(stripped) or is_section_heading(stripped):
            continue

        alinea_match = ALINEA_START_RE.match(stripped)
        if alinea_match:
            num = int(alinea_match.group("num"))
            text = strip_leading_amendments(alinea_match.group("text").strip())
            if is_amendment_only(text):
                add_paragraph(text, num)
            elif text:
                add_paragraph(text, num)
            continue

        note_match = ALINEA_NOTE_LINE_RE.match(stripped)
        if note_match:
            nums = parse_alinea_numbers(note_match.group("nums"))
            body = note_match.group("body").strip()
            for num in nums:
                if body:
                    add_paragraph(body, num)
                else:
                    add_paragraph(stripped, num)
            continue

        if is_amendment_only(stripped):
            add_paragraph(stripped)
            continue

        add_paragraph(strip_leading_amendments(stripped))

    return paragraphs


def parse_law_text(
    content: str,
    *,
    title: str | None = None,
    source_url: str | None = None,
    retrieved_at: str | None = None,
) -> dict:
    lines = content.splitlines()
    stop_idx = len(lines)
    for idx, line in enumerate(lines):
        lower = line.strip().lower()
        if any(lower.startswith(marker) for marker in STOP_SECTION_MARKERS):
            stop_idx = idx
            break

    lines = lines[:stop_idx]

    if title is None:
        for line in lines:
            candidate = line.strip()
            if candidate and not is_noise_line(candidate):
                title = normalize_title(candidate)
                break
        else:
            title = ""

    articles: list[dict] = []
    current_match = None
    current_body = ""
    current_continuations: list[str] = []

    def flush_article() -> None:
        nonlocal current_match, current_body, current_continuations
        if not current_match:
            return
        label = format_article_label(
            current_match.group("label"), current_match.group("num")
        )
        paragraphs = parse_article_body(current_body, current_continuations)
        article_text = " ".join(p["text"] for p in paragraphs).strip()
        articles.append(
            {
                "article": label,
                "text": article_text,
                "paragraphs": paragraphs,
            }
        )
        current_match = None
        current_body = ""
        current_continuations = []

    for line in lines[1:]:
        stripped = line.strip()
        if is_noise_line(stripped):
            continue

        article_match = ARTICLE_RE.match(stripped)
        if article_match:
            flush_article()
            current_match = article_match
            current_body = article_match.group("body")
            current_continuations = []
            continue

        if current_match is not None:
            current_continuations.append(line)

    flush_article()

    return {
        "title": title,
        "source_url": source_url or DEFAULT_SOURCE_URL,
        "retrieved_at": retrieved_at or date.today().isoformat(),
        "articles": articles,
    }


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
        print(
            "Usage: python parser.py <input.txt> [output.json]\n"
            "Quote paths that contain spaces."
        )
        return

    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    elif len(sys.argv) > 1:
        output_path = input_path.with_suffix(".json")
    else:
        output_path = None

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Input file not found: {input_path}\n"
            "If the path contains spaces, wrap it in quotes."
        )

    content = input_path.read_text(encoding="utf-8")
    result = parse_law_text(content)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if output_path:
        output_path.write_text(output, encoding="utf-8")
        message = f"Parsed {len(result['articles'])} articles -> {output_path}"
        try:
            print(message)
        except UnicodeEncodeError:
            print(f"Parsed {len(result['articles'])} articles.")
    else:
        print(output)


if __name__ == "__main__":
    main()
