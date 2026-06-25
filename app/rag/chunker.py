"""
Фаза 5: Legal chunking за RAG.

Правило:
  - 1 chunk = 1 член (предпочитано)
  - ако членът е твърде дълъг → по 1 chunk на алинея

Вход: normalized documents (data/normalized/*.json) или parsed law JSON
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.db.models import Document, LegalChunk
from app.integration.normalizer import (
    load_parsed_law,
    make_document_id,
    normalize_parsed_law,
    slugify_article,
    slugify_law,
)

DEFAULT_NORMALIZED_DIR = Path(__file__).resolve().parents[2] / "data" / "normalized"
DEFAULT_CHUNKS_DIR = Path(__file__).resolve().parents[2] / "data" / "chunks"
DEFAULT_MAX_ARTICLE_CHARS = 2000


def format_chunk_text(article: str, paragraph: str | None, body: str) -> str:
    prefix = article
    if paragraph:
        prefix = f"{article}, {paragraph}"
    return f"{prefix}. {body}"


def make_chunk_id(law_slug: str, article: str, paragraph: str | None) -> str:
    article_part = slugify_article(article)
    if paragraph:
        paragraph_part = paragraph.lower().replace("ал.", "al").replace(" ", "")
        return f"{law_slug}_{article_part}_{paragraph_part}"
    return f"{law_slug}_{article_part}"


def chunk_documents(
    documents: list[Document],
    *,
    max_article_chars: int = DEFAULT_MAX_ARTICLE_CHARS,
) -> list[LegalChunk]:
    grouped: dict[str, list[Document]] = {}
    article_order: list[str] = []
    for doc in documents:
        if doc.article_number not in grouped:
            article_order.append(doc.article_number)
        grouped.setdefault(doc.article_number, []).append(doc)

    chunks: list[LegalChunk] = []
    law_slug = slugify_law(documents[0].law_title) if documents else "law"

    for article_number in article_order:
        article_docs = grouped[article_number]
        law_title = article_docs[0].law_title
        source_url = article_docs[0].source_url
        retrieved_at = article_docs[0].retrieved_at

        full_text = " ".join(doc.text for doc in article_docs).strip()
        article_header = f"{article_number}."
        full_with_header = format_chunk_text(
            article_number, None, full_text.removeprefix(article_header).strip()
        )

        if len(full_with_header) <= max_article_chars:
            chunks.append(
                LegalChunk(
                    chunk_id=make_document_id(law_slug, article_number, None, 0),
                    law=law_title,
                    article=article_number,
                    paragraph=None,
                    text=full_with_header,
                    metadata={
                        "source_url": source_url,
                        "retrieved_at": retrieved_at,
                    },
                )
            )
            continue

        for doc in article_docs:
            chunks.append(
                LegalChunk(
                    chunk_id=doc.id,
                    law=law_title,
                    article=article_number,
                    paragraph=doc.paragraph_number,
                    text=format_chunk_text(
                        article_number, doc.paragraph_number, doc.text
                    ),
                    metadata={
                        "source_url": source_url,
                        "retrieved_at": retrieved_at,
                    },
                )
            )

    return chunks


def chunk_parsed_law(
    parsed: dict,
    *,
    max_article_chars: int = DEFAULT_MAX_ARTICLE_CHARS,
) -> list[LegalChunk]:
    documents = normalize_parsed_law(parsed)
    return chunk_documents(documents, max_article_chars=max_article_chars)


def load_documents(path: Path) -> list[Document]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Document(**row) for row in payload["documents"]]


def save_chunks(chunks: list[LegalChunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(chunks),
        "chunks": [chunk.to_dict() for chunk in chunks],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def chunk_file(
    input_path: Path,
    output_path: Path | None = None,
    *,
    max_article_chars: int = DEFAULT_MAX_ARTICLE_CHARS,
    from_parsed: bool = False,
) -> list[LegalChunk]:
    if from_parsed:
        parsed = load_parsed_law(input_path)
        chunks = chunk_parsed_law(parsed, max_article_chars=max_article_chars)
    else:
        documents = load_documents(input_path)
        chunks = chunk_documents(documents, max_article_chars=max_article_chars)

    if output_path:
        save_chunks(chunks, output_path)
    return chunks


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
        print(
            "Usage: python -m app.rag.chunker <input.json> [output.json]\n"
            "Builds RAG chunks from normalized documents (default) or parsed law (--parsed)."
        )
        return

    from_parsed = "--parsed" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--parsed"]

    input_path = (
        Path(args[0])
        if args
        else DEFAULT_NORMALIZED_DIR
        / "закон-за-административни-надушения-и-наказания.json"
    )
    if len(args) > 1:
        output_path = Path(args[1])
    else:
        output_path = DEFAULT_CHUNKS_DIR / input_path.name

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    chunks = chunk_file(
        input_path,
        output_path,
        from_parsed=from_parsed,
    )
    print(f"Created {len(chunks)} chunks -> {output_path}")


if __name__ == "__main__":
    main()
