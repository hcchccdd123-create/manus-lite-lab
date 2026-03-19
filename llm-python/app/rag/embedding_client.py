from __future__ import annotations

import httpx

from app.core.errors import RAGError, RAGUnavailableError


class GLMEmbeddingClient:
    def __init__(self, *, base_url: str, api_key: str, model: str, timeout_seconds: int):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

    def _embedding_urls(self) -> list[str]:
        base = self.base_url
        urls = [f'{base}/embeddings']
        if '/v4' not in base:
            urls.append(f'{base}/v4/embeddings')
        deduped: list[str] = []
        for url in urls:
            if url not in deduped:
                deduped.append(url)
        return deduped

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise RAGError('GLM embedding API key is not configured')
        if not texts:
            return []

        payload = {'model': self.model, 'input': texts}
        last_error: Exception | None = None

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                for url in self._embedding_urls():
                    try:
                        resp = await client.post(url, headers=self._headers(), json=payload)
                        resp.raise_for_status()
                        data = resp.json()
                        rows = data.get('data', [])
                        embeddings = [item.get('embedding') for item in rows if item.get('embedding')]
                        if len(embeddings) != len(texts):
                            raise RAGError('GLM embedding response size mismatch')
                        return embeddings
                    except httpx.HTTPStatusError as exc:
                        last_error = exc
                        if exc.response.status_code == 404:
                            continue
                        raise RAGUnavailableError(f'GLM embedding request failed: status={exc.response.status_code}') from exc
        except httpx.TimeoutException as exc:
            raise RAGUnavailableError('GLM embedding timeout') from exc
        except httpx.HTTPError as exc:
            raise RAGUnavailableError(f'GLM embedding unavailable: {exc}') from exc

        if last_error is not None:
            raise RAGUnavailableError('GLM embedding endpoint not found') from last_error
        raise RAGUnavailableError('GLM embedding unavailable')
