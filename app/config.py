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


def get_settings() -> Settings:
    return Settings()
