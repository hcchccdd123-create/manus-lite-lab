from collections.abc import AsyncGenerator

import httpx

from app.core.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.providers.base import ChatChunk, ChatRequest, ChatResponse


class GLMProvider:
    name = 'glm'

    def __init__(self, base_url: str, api_key: str, timeout_seconds: int):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

    async def chat(self, req: ChatRequest) -> ChatResponse:
        payload = {
            'model': req.model,
            'messages': [m.model_dump() for m in req.messages],
            'temperature': req.temperature,
            'max_tokens': req.max_tokens,
            'stream': False,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f'{self.base_url}/v1/chat/completions', headers=self._headers(), json=payload)
            self._raise_for_status(resp)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError('GLM timeout') from exc
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc.response) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f'GLM unavailable: {exc}') from exc

        data = resp.json()
        choice = data.get('choices', [{}])[0]
        text = choice.get('message', {}).get('content', '')
        return ChatResponse(text=text, usage=data.get('usage'), raw=data)

    async def stream_chat(self, req: ChatRequest) -> AsyncGenerator[ChatChunk, None]:
        payload = {
            'model': req.model,
            'messages': [m.model_dump() for m in req.messages],
            'temperature': req.temperature,
            'max_tokens': req.max_tokens,
            'stream': True,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream('POST', f'{self.base_url}/v1/chat/completions', headers=self._headers(), json=payload) as resp:
                    self._raise_for_status(resp)
                    async for line in resp.aiter_lines():
                        if not line.startswith('data:'):
                            continue
                        data_line = line[5:].strip()
                        if data_line == '[DONE]':
                            yield ChatChunk(delta='', finish_reason='stop')
                            break
                        data = httpx.Response(200, text=data_line).json()
                        delta = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                        if delta:
                            yield ChatChunk(delta=delta)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError('GLM stream timeout') from exc
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc.response) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f'GLM stream unavailable: {exc}') from exc

    def _raise_for_status(self, resp: httpx.Response) -> None:
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            raise

    def _map_http_error(self, resp: httpx.Response):
        if resp.status_code in (401, 403):
            return ProviderAuthError('GLM auth error')
        if resp.status_code == 429:
            return ProviderRateLimitError('GLM rate limited')
        return ProviderUnavailableError(f'GLM status={resp.status_code}')

    async def health_check(self) -> bool:
        return bool(self.base_url and self.api_key)
