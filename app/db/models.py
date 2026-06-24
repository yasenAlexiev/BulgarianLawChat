from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Document:
    """MVP normalized row — one article paragraph (or whole article)."""

    id: str
    law_title: str
    article_number: str
    paragraph_number: str | None
    text: str
    source_url: str
    retrieved_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LegalChunk:
    """RAG chunk — one article, or one paragraph if the article is too long."""

    chunk_id: str
    law: str
    article: str
    paragraph: str | None
    text: str
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
