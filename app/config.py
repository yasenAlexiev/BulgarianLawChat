from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+psycopg2://lawchat:lawchat@127.0.0.1:5433/lawchat"
    )
    embedding_provider: str = "local"
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_dimension: int = 1024
    openai_api_key: str = ""
    init_db_on_startup: bool = True
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    retrieval_top_k: int = 16
    context_top_k: int = 8
    rerank_enabled: bool = True
    rerank_model: str = "BAAI/bge-reranker-v2-m3"


def get_settings() -> Settings:
    return Settings()
