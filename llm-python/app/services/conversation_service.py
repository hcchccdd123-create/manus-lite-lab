from app.core.config import Settings
from app.core.errors import NotFoundError
from app.db.repositories.conversation_repo import ConversationRepository


class ConversationService:
    def __init__(self, settings: Settings, repo: ConversationRepository):
        self.settings = settings
        self.repo = repo

    async def create(self, title: str | None, provider: str | None, model: str | None, system_prompt: str | None, memory_window_size: int | None):
        provider_name = provider or self.settings.default_provider
        model_name = model or self._default_model(provider_name)
        return await self.repo.create(
            title=title or 'New Chat',
            provider=provider_name,
            model=model_name,
            system_prompt=system_prompt,
            memory_window_size=memory_window_size or self.settings.memory_window_size,
        )

    async def get_or_raise(self, session_id: str):
        conv = await self.repo.get(session_id)
        if not conv:
            raise NotFoundError(f'conversation not found: {session_id}')
        return conv

    async def list(self, status: str | None, limit: int, offset: int):
        return await self.repo.list(status, limit, offset)

    async def update(self, session_id: str, **kwargs):
        conv = await self.get_or_raise(session_id)
        if kwargs.get('provider') and not kwargs.get('model'):
            kwargs['model'] = self._default_model(kwargs['provider'])
        return await self.repo.update(conv, **kwargs)

    def _default_model(self, provider_name: str) -> str:
        if provider_name == 'ollama':
            return self.settings.default_model_ollama
        if provider_name == 'glm':
            return self.settings.glm_model
        return self.settings.codex_model
