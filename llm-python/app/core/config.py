from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = 'dev'
    host: str = '0.0.0.0'
    port: int = 8000

    db_url: str = 'sqlite+aiosqlite:///./data/chat.db'

    default_provider: str = 'ollama'
    default_model_ollama: str = 'qwen3.5:0.8b'

    ollama_base_url: str = 'http://127.0.0.1:11434'
    glm_api_key: str = ''
    glm_base_url: str = ''
    glm_model: str = 'glm-4.7'
    codex_api_key: str = ''
    codex_base_url: str = ''
    codex_model: str = 'gpt-4.1-mini'

    memory_window_size: int = 12
    summary_trigger_messages: int = 20
    max_context_chars: int = 16000

    enable_provider_fallback: bool = False
    provider_timeout_seconds: int = Field(default=60, ge=1, le=300)


@lru_cache
def get_settings() -> Settings:
    return Settings()
