from __future__ import annotations

import re
import unicodedata


def clean_question(question: str) -> str:
    """Normalize user input before embedding and retrieval."""
    text = unicodedata.normalize("NFKC", question.strip())
    text = re.sub(r"\s+", " ", text)
    return text
