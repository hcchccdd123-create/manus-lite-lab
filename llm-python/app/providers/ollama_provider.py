from collections.abc import AsyncGenerator

import httpx

from app.core.errors import ProviderTimeoutError, ProviderUnavailableError
from app.providers.base import ChatChunk, ChatRequest, ChatResponse


class OllamaProvider:
    name = 'ollama'

    def __init__(self, base_url: str, timeout_seconds: int):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout_seconds

    @staticmethod
    def _build_options(req: ChatRequest) -> dict:
        options = {'temperature': req.temperature}
        if req.top_p is not None:
            options['top_p'] = req.top_p
        if req.repeat_penalty is not None:
            options['repeat_penalty'] = req.repeat_penalty
        return options

    async def chat(self, req: ChatRequest) -> ChatResponse:
        enable_thinking = req.enable_thinking if req.enable_thinking is not None else True
        payload = {
            'model': req.model,
            'messages': [m.model_dump() for m in req.messages],
            'stream': False,
            'think': enable_thinking,
            'options': self._build_options(req),
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f'{self.base_url}/api/chat', json=payload)
            resp.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError('Ollama timeout') from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f'Ollama unavailable: {exc}') from exc

        data = resp.json()
        message = data.get('message', {})
        usage = {
            'prompt_tokens': data.get('prompt_eval_count'),
            'completion_tokens': data.get('eval_count'),
            'total_tokens': (data.get('prompt_eval_count') or 0) + (data.get('eval_count') or 0),
        }
        return ChatResponse(text=message.get('content', ''), usage=usage, raw=data)

    async def stream_chat(self, req: ChatRequest) -> AsyncGenerator[ChatChunk, None]:
        enable_thinking = req.enable_thinking if req.enable_thinking is not None else True
        payload = {
            'model': req.model,
            'messages': [m.model_dump() for m in req.messages],
            'stream': True,
            'think': enable_thinking,
            'options': self._build_options(req),
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream('POST', f'{self.base_url}/api/chat', json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        chunk = httpx.Response(200, text=line).json()
                        msg = chunk.get('message', {})
                        delta = msg.get('content', '')
                        thinking_delta = msg.get('thinking', '')
                        if thinking_delta:
                            yield ChatChunk(delta='', thinking=thinking_delta)
                        if delta:
                            yield ChatChunk(delta=delta)
                        if chunk.get('done'):
                            yield ChatChunk(delta='', finish_reason='stop')
                            break
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError('Ollama stream timeout') from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f'Ollama stream unavailable: {exc}') from exc

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f'{self.base_url}/api/tags')
            return resp.status_code == 200
        except Exception:
            return False
