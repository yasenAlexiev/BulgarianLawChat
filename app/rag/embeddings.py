from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import Settings, get_settings


class Embedder(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        pass


class OpenAIEmbedder(Embedder):
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        from openai import OpenAI

        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.embedding_model
        self._dimension = settings.embedding_dimension

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(
            model=self._model,
            input=texts,
            dimensions=self._dimension,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class LocalEmbedder(Embedder):
    """Sentence-transformers backend; E5 models need query/passage prefixes."""

    def __init__(self, settings: Settings) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(settings.embedding_model)
        self._model_name = settings.embedding_model
        self._dimension = settings.embedding_dimension
        self._is_e5 = "e5" in settings.embedding_model.lower()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def _prefix_documents(self, texts: list[str]) -> list[str]:
        if not self._is_e5:
            return texts
        return [f"passage: {text}" for text in texts]

    def _prefix_query(self, text: str) -> str:
        if not self._is_e5:
            return text
        return f"query: {text}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            self._prefix_documents(texts),
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self._model.encode(
            self._prefix_query(text),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vector.tolist()


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        settings = get_settings()
        if settings.embedding_provider == "openai":
            _embedder = OpenAIEmbedder(settings)
        else:
            _embedder = LocalEmbedder(settings)
    return _embedder
