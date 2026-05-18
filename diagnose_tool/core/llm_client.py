"""OpenAI-compatible LLM HTTP client."""

from __future__ import annotations

import logging
from threading import Semaphore
from typing import Any

import httpx

from diagnose_tool.core.llm_config import AppLLMConfig

logger = logging.getLogger(__name__)


class LLMClientError(RuntimeError):
    """Raised on LLM API errors (non-2xx, network, timeout)."""


class LLMClient:
    """OpenAI-compatible LLM HTTP client with concurrency limiting."""

    _semaphore: Semaphore | None = None  # class-level shared semaphore

    def __init__(self, config: AppLLMConfig) -> None:
        self._config = config
        # Class-level semaphore ensures shared limit across instances
        if LLMClient._semaphore is None:
            LLMClient._semaphore = Semaphore(5)
        self._semaphore = LLMClient._semaphore

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> str:
        """Call OpenAI-compatible /chat/completions endpoint.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Override model (defaults to config model).
            base_url: Override base URL (defaults to config base_url).
            api_key: Override API key (defaults to config api_key).
            timeout: Override timeout in seconds (defaults to config timeout).

        Returns:
            The content string of the first assistant message.

        Raises:
            LLMClientError: On non-2xx response, network error, or timeout.
        """
        resolved_model = model if model is not None else self._config.model
        resolved_base_url = base_url if base_url is not None else self._config.base_url
        resolved_api_key = api_key if api_key is not None else self._config.api_key
        resolved_timeout = timeout if timeout is not None else self._config.timeout

        url = f"{resolved_base_url.rstrip('/')}/chat/completions"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if resolved_api_key:
            headers["Authorization"] = f"Bearer {resolved_api_key}"

        body: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
        }

        with self._semaphore:
            try:
                with httpx.Client(timeout=resolved_timeout) as client:
                    response = client.post(url, headers=headers, json=body)
            except httpx.TimeoutException:
                raise LLMClientError("LLM API request timed out")
            except httpx.RequestError as exc:
                raise LLMClientError(f"LLM API request failed: {exc}")

        if not response.is_success:
            raise LLMClientError(f"LLM API returned {response.status_code}")

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise LLMClientError("LLM API response has no choices")

        message = choices[0].get("message", {})
        content = message.get("content", "")
        if not content:
            raise LLMClientError("LLM API response message has no content")

        return content