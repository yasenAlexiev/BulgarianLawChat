"""
Фаза 4: Нормализация на парснат закон.

Вход: JSON от parser.py (data/processed/*.json)
Изход: плоски documents с запазена структура член → алинея
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

from app.db.models import Document

INLINE_ALINEA_PREFIX_RE = re.compile(r"^\(\d+\)\s*")
SECTION_FRAGMENT_RE = re.compile(
    r"^(?:Раздел|Глава|Част|Параграф)\s+",
    re.IGNORECASE,
)
AMENDMENT_ONLY_RE = re.compile(
    r"^\((?:Отм|Изм|Нов|Доп|Попр|Предишен|Предишна|Зал|Ал\.)",
    re.IGNORECASE,
)

DEFAULT_PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
DEFAULT_NORMALIZED_DIR = Path(__file__).resolve().parents[2] / "data" / "normalized"


def slugify_law(title: str) -> str:
    """Кратък идентификатор за закона, напр. zann за ЗАНН."""
    words = re.findall(r"[а-яА-Яa-zA-Z0-9]+", title.lower())
    skip = {
        "закон",
        "за",
        "и",
        "на",
        "в",
        "от",
        "по",
        "с",
        "кодекс",
        "the",
    }
    letters = [word[0] for word in words if word not in skip and word]
    slug = "".join(letters)
    return slug[:12] or "law"


def slugify_article(article: str) -> str:
    """чл. 28а -> chl_28a"""
    normalized = article.lower().replace("чл.", "chl").replace("§", "par")
    normalized = re.sub(r"[^\w]+", "_", normalized)
    return normalized.strip("_")


def slugify_paragraph(paragraph: str | None) -> str:
    if not paragraph:
        return "full"
    normalized = paragraph.lower().replace("ал.", "al")
    normalized = re.sub(r"[^\w]+", "_", normalized)
    return normalized.strip("_")


def clean_unit_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return INLINE_ALINEA_PREFIX_RE.sub("", text).strip()


def is_section_fragment(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if SECTION_FRAGMENT_RE.match(stripped):
        return True
    if len(stripped) < 80 and stripped == stripped.upper() and " " in stripped:
        return True
    return False


def make_document_id(
    law_slug: str, article: str, paragraph: str | None, order_index: int
) -> str:
    return f"{law_slug}_{slugify_article(article)}_{slugify_paragraph(paragraph)}_{order_index}"


def normalize_parsed_law(parsed: dict) -> list[Document]:
    law_title = parsed["title"].strip()
    source_url = parsed["source_url"]
    retrieved_at = parsed["retrieved_at"]
    law_slug = slugify_law(law_title)

    documents: list[Document] = []
    order_index = 0

    for article in parsed.get("articles", []):
        article_number = article["article"].strip()
        paragraphs = article.get("paragraphs") or []

        if not paragraphs:
            text = clean_unit_text(article.get("text", ""))
            if not text:
                continue
            documents.append(
                Document(
                    id=make_document_id(law_slug, article_number, None, order_index),
                    law_title=law_title,
                    article_number=article_number,
                    paragraph_number=None,
                    text=text,
                    source_url=source_url,
                    retrieved_at=retrieved_at,
                )
            )
            order_index += 1
            continue

        for paragraph in paragraphs:
            paragraph_number = paragraph.get("paragraph")
            text = clean_unit_text(paragraph.get("text", ""))
            if not text or is_section_fragment(text):
                continue
            if AMENDMENT_ONLY_RE.match(text) and len(text) < 120:
                # Запазваме отменени алинеи — важни са за правния контекст.
                pass

            documents.append(
                Document(
                    id=make_document_id(
                        law_slug, article_number, paragraph_number, order_index
                    ),
                    law_title=law_title,
                    article_number=article_number,
                    paragraph_number=paragraph_number,
                    text=text,
                    source_url=source_url,
                    retrieved_at=retrieved_at,
                )
            )
            order_index += 1

    return documents


def load_parsed_law(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_documents(documents: list[Document], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(documents),
        "documents": [doc.to_dict() for doc in documents],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def normalize_file(input_path: Path, output_path: Path | None = None) -> list[Document]:
    parsed = load_parsed_law(input_path)
    documents = normalize_parsed_law(parsed)
    if output_path:
        save_documents(documents, output_path)
    return documents


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
        print(
            "Usage: python -m app.integration.normalizer <input.json> [output.json]\n"
            "Normalizes parser output into flat legal documents."
        )
        return

    input_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else DEFAULT_PROCESSED_DIR
        / "закон-за-административни-надушения-и-наказания.json"
    )
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        output_path = DEFAULT_NORMALIZED_DIR / input_path.name

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    documents = normalize_file(input_path, output_path)
    print(f"Normalized {len(documents)} documents -> {output_path}")


if __name__ == "__main__":
    main()
