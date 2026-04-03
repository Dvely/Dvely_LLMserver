import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.errors import APIError
from app.core.logging import get_logger

logger = get_logger("gateway.ollama")


class OllamaClient:
    def __init__(self, base_url: str, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Ollama client is not initialized")
        return self._client

    async def check_ready(self) -> bool:
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self.client.post("/api/chat", json=payload)
            if response.status_code >= 400:
                detail = response.text
                logger.error("ollama_error status=%s body=%s", response.status_code, detail)
                raise APIError(502, "upstream_error", "Ollama returned an error")
            return response.json()
        except httpx.TimeoutException as exc:
            logger.error("ollama_timeout error=%s", str(exc))
            raise APIError(504, "timeout_error", "Upstream Ollama timeout") from exc
        except httpx.HTTPError as exc:
            logger.error("ollama_unavailable error=%s", str(exc))
            raise APIError(503, "api_connection_error", "Ollama unavailable") from exc

    async def stream_chat(self, payload: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        try:
            async with self.client.stream("POST", "/api/chat", json=payload) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    logger.error("ollama_stream_error status=%s body=%s", response.status_code, detail.decode("utf-8", errors="ignore"))
                    raise APIError(502, "upstream_error", "Ollama returned an error")

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        logger.error("ollama_stream_parse_error line=%s", line)
        except httpx.TimeoutException as exc:
            logger.error("ollama_stream_timeout error=%s", str(exc))
            raise APIError(504, "timeout_error", "Upstream Ollama timeout") from exc
        except httpx.HTTPError as exc:
            logger.error("ollama_stream_unavailable error=%s", str(exc))
            raise APIError(503, "api_connection_error", "Ollama unavailable") from exc
