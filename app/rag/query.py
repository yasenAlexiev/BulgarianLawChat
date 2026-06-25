from __future__ import annotations

import re
import unicodedata


def clean_question(question: str) -> str:
    """Normalize user input before embedding and retrieval."""
    text = unicodedata.normalize("NFKC", question.strip())
    text = re.sub(r"\s+", " ", text)
    return text


def retrieval_queries(question: str) -> list[str]:
    """Build one or more search queries to improve recall on legal questions."""
    primary = clean_question(question)
    queries = [primary]
    lower = primary.lower()

    rights_terms = ("права", "право", "обезщетение", "оспор")
    termination_terms = ("уволн", "прекрат", "без предизвестие")
    if any(term in lower for term in rights_terms) and any(
        term in lower for term in termination_terms
    ):
        queries.append(
            clean_question(
                f"{primary} обезщетение оспорване незаконно уволнение работник"
            )
        )

    return queries
