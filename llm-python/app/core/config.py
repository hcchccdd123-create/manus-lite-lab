from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = 'dev'
    host: str = '0.0.0.0'
    port: int = 8000

    db_url: str = 'sqlite+aiosqlite:///./data/chat.db'

    default_provider: str = 'glm'
    default_model_ollama: str = 'qwen3.5:0.8b'

    ollama_base_url: str = 'http://127.0.0.1:11434'
    glm_api_key: str = ''
    glm_base_url: str = 'https://open.bigmodel.cn/api/paas/v4'
    glm_model: str = 'glm-4.7'
    codex_api_key: str = ''
    codex_base_url: str = ''
    codex_model: str = 'gpt-4.1-mini'

    memory_window_size: int = 12
    summary_trigger_messages: int = 20
    max_context_chars: int = 16000

    generation_top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    generation_repeat_penalty: float = Field(default=1.12, ge=0.8, le=2.0)

    enable_thinking_loop_guard: bool = True
    thinking_loop_max_chars: int = Field(default=12000, ge=1000, le=100000)
    thinking_loop_repeat_window: int = Field(default=14, ge=4, le=100)
    thinking_loop_repeat_threshold: int = Field(default=4, ge=2, le=20)

    enable_provider_fallback: bool = False
    provider_timeout_seconds: int = Field(default=60, ge=1, le=300)


@lru_cache
def get_settings() -> Settings:
    return Settings()
