from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    DATABASE_URL: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/finaciero'
    OPENAI_API_KEY: str | None = None
    APP_ENV: str = 'development'
    SECRET_KEY: str = 'change-me'

    EMBEDDING_MODEL: str = 'text-embedding-3-small'
    EMBEDDING_DIM: int = 1536
    LLM_MODEL: str = 'gpt-4o-mini'
    CHUNK_SIZE: int = 900
    CHUNK_OVERLAP: int = 150


@lru_cache
def get_settings() -> Settings:
    return Settings()
