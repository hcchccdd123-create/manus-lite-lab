import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ProviderError
from app.db.models import ProviderCallLog
from app.providers.base import ChatRequest, ChatResponse
from app.providers.factory import ProviderFactory
from app.utils.ids import new_log_id

logger = logging.getLogger(__name__)


class ProviderRouter:
    def __init__(self, settings: Settings, db: AsyncSession):
        self.settings = settings
        self.db = db
        self.providers = ProviderFactory(settings).build()

    async def _save_call_log(
        self,
        *,
        request_id: str,
        conversation_id: str,
        provider: str,
        model: str,
        success: bool,
        latency_ms: int,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        log = ProviderCallLog(
            id=new_log_id(),
            request_id=request_id,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            success=1 if success else 0,
            latency_ms=latency_ms,
            error_code=error_code,
            error_message=error_message[:255] if error_message else None,
        )
        self.db.add(log)
        await self.db.commit()

    async def chat(self, req: ChatRequest, *, conversation_id: str, request_id: str) -> ChatResponse:
        chain = [req.provider]
        if self.settings.enable_provider_fallback:
            for item in ['ollama', 'glm', 'codex']:
                if item not in chain:
                    chain.append(item)

        last_err: Exception | None = None
        for provider_name in chain:
            provider = self.providers[provider_name]
            started = time.perf_counter()
            try:
                alt_model = req.model if provider_name == req.provider else self._default_model(provider_name)
                alt_req = req.model_copy(update={'provider': provider_name, 'model': alt_model})
                resp = await provider.chat(alt_req)
                await self._save_call_log(
                    request_id=request_id,
                    conversation_id=conversation_id,
                    provider=provider_name,
                    model=alt_req.model,
                    success=True,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )
                return resp
            except ProviderError as err:
                last_err = err
                await self._save_call_log(
                    request_id=request_id,
                    conversation_id=conversation_id,
                    provider=provider_name,
                    model=req.model,
                    success=False,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    error_code=err.code,
                    error_message=err.message,
                )
                logger.warning('provider failed provider=%s err=%s', provider_name, err.code)
                if not self.settings.enable_provider_fallback:
                    break

        if last_err:
            raise last_err
        raise ProviderError('No provider available')

    async def stream_chat(self, req: ChatRequest, *, conversation_id: str, request_id: str):
        provider = self.providers[req.provider]
        started = time.perf_counter()
        try:
            async for chunk in provider.stream_chat(req):
                yield chunk
            await self._save_call_log(
                request_id=request_id,
                conversation_id=conversation_id,
                provider=req.provider,
                model=req.model,
                success=True,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except ProviderError as err:
            await self._save_call_log(
                request_id=request_id,
                conversation_id=conversation_id,
                provider=req.provider,
                model=req.model,
                success=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error_code=err.code,
                error_message=err.message,
            )
            raise

    def _default_model(self, provider_name: str) -> str:
        if provider_name == 'ollama':
            return self.settings.default_model_ollama
        if provider_name == 'glm':
            return self.settings.glm_model
        return self.settings.codex_model
