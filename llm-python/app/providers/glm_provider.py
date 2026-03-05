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

    @staticmethod
    def _attach_thinking(payload: dict, enable_thinking: bool | None) -> None:
        if enable_thinking is None:
            return
        payload['thinking'] = {'type': 'enabled' if enable_thinking else 'disabled'}

    @staticmethod
    def _without_thinking(payload: dict) -> dict:
        next_payload = dict(payload)
        next_payload.pop('thinking', None)
        return next_payload

    @staticmethod
    def _should_retry_without_thinking(resp: httpx.Response, payload: dict) -> bool:
        return resp.status_code == 400 and 'thinking' in payload

    def _chat_urls(self) -> list[str]:
        base = self.base_url
        urls = [f'{base}/chat/completions']
        if '/v4' not in base:
            urls.append(f'{base}/v4/chat/completions')
        if '/v1' not in base:
            urls.append(f'{base}/v1/chat/completions')
        deduped: list[str] = []
        for url in urls:
            if url not in deduped:
                deduped.append(url)
        return deduped

    async def chat(self, req: ChatRequest) -> ChatResponse:
        payload = {
            'model': req.model,
            'messages': [m.model_dump() for m in req.messages],
            'temperature': req.temperature,
            'top_p': req.top_p,
            'max_tokens': req.max_tokens,
            'stream': False,
        }
        if req.top_p is None:
            payload.pop('top_p')
        self._attach_thinking(payload, req.enable_thinking)
        resp: httpx.Response | None = None
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for url in self._chat_urls():
                    resp = await client.post(url, headers=self._headers(), json=payload)
                    if self._should_retry_without_thinking(resp, payload):
                        payload = self._without_thinking(payload)
                        resp = await client.post(url, headers=self._headers(), json=payload)
                    if resp.status_code == 404:
                        continue
                    self._raise_for_status(resp)
                    break
            if resp is None:
                raise ProviderUnavailableError('GLM unavailable: missing response')
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
            'top_p': req.top_p,
            'max_tokens': req.max_tokens,
            'stream': True,
        }
        if req.top_p is None:
            payload.pop('top_p')
        self._attach_thinking(payload, req.enable_thinking)
        last_http_error: httpx.HTTPStatusError | None = None
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for url in self._chat_urls():
                    current_payload = payload
                    try:
                        async for chunk in self._stream_payload(client, url, current_payload):
                            yield chunk
                        return
                    except httpx.HTTPStatusError as exc:
                        last_http_error = exc
                        if self._should_retry_without_thinking(exc.response, current_payload):
                            current_payload = self._without_thinking(current_payload)
                            try:
                                async for chunk in self._stream_payload(client, url, current_payload):
                                    yield chunk
                                return
                            except httpx.HTTPStatusError as retry_exc:
                                last_http_error = retry_exc
                                if retry_exc.response.status_code == 404:
                                    continue
                                raise
                        if exc.response.status_code == 404:
                            continue
                        raise
                if last_http_error is not None:
                    raise last_http_error
                raise ProviderUnavailableError('GLM stream unavailable: no endpoint succeeded')
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

    async def _stream_payload(self, client: httpx.AsyncClient, url: str, payload: dict) -> AsyncGenerator[ChatChunk, None]:
        async with client.stream('POST', url, headers=self._headers(), json=payload) as resp:
            self._raise_for_status(resp)
            async for line in resp.aiter_lines():
                if not line.startswith('data:'):
                    continue
                data_line = line[5:].strip()
                if data_line == '[DONE]':
                    yield ChatChunk(delta='', finish_reason='stop')
                    break
                data = httpx.Response(200, text=data_line).json()
                delta_data = data.get('choices', [{}])[0].get('delta', {})
                thinking_delta = delta_data.get('reasoning_content', '')
                text_delta = delta_data.get('content', '')
                if thinking_delta:
                    yield ChatChunk(delta='', thinking=thinking_delta)
                if text_delta:
                    yield ChatChunk(delta=text_delta)
