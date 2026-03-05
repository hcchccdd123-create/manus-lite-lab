from app.core.config import Settings
from app.providers.codex_provider import CodexProvider
from app.providers.glm_provider import GLMProvider
from app.providers.ollama_provider import OllamaProvider


class ProviderFactory:
    def __init__(self, settings: Settings):
        self.settings = settings

    def build(self) -> dict[str, object]:
        return {
            'ollama': OllamaProvider(
                base_url=self.settings.ollama_base_url,
                timeout_seconds=self.settings.provider_timeout_seconds,
            ),
            'glm': GLMProvider(
                base_url=self.settings.glm_base_url,
                api_key=self.settings.glm_api_key,
                timeout_seconds=self.settings.provider_timeout_seconds,
            ),
            'codex': CodexProvider(
                base_url=self.settings.codex_base_url,
                api_key=self.settings.codex_api_key,
                timeout_seconds=self.settings.provider_timeout_seconds,
            ),
        }
