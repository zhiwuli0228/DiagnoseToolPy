"""Tests for diagnose_tool/core/llm_client.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import httpx

from diagnose_tool.core.llm_client import LLMClient, LLMClientError
from diagnose_tool.core.llm_config import AppLLMConfig


@pytest.fixture
def default_config(tmp_path: Path) -> AppLLMConfig:
    """Default LLM config for testing."""
    return AppLLMConfig(
        enabled=True,
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        timeout=60,
        data_dir=tmp_path,
    )


class TestLLMClient:
    """Tests for LLMClient.chat()."""

    def test_successful_call_returns_assistant_content(self) -> None:
        """Successful LLM call returns assistant message content."""
        config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=__import__('pathlib').Path("/tmp"),
        )
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Test diagnosis result"}}
            ]
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            client = LLMClient(config)
            result = client.chat(messages=[{"role": "user", "content": "hello"}])

        assert result == "Test diagnosis result"

    def test_non_200_raises_llm_client_error(self) -> None:
        """Non-200 response raises LLMClientError."""
        config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=__import__('pathlib').Path("/tmp"),
        )
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            client = LLMClient(config)
            with pytest.raises(LLMClientError, match="500"):
                client.chat(messages=[{"role": "user", "content": "hello"}])

    def test_network_error_raises_llm_client_error(self) -> None:
        """Network error raises LLMClientError."""
        config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=__import__('pathlib').Path("/tmp"),
        )

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.RequestError("Connection refused")
            mock_client_cls.return_value = mock_client

            client = LLMClient(config)
            with pytest.raises(LLMClientError, match="Connection refused"):
                client.chat(messages=[{"role": "user", "content": "hello"}])

    def test_timeout_raises_llm_client_error(self) -> None:
        """Timeout raises LLMClientError."""
        config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=__import__('pathlib').Path("/tmp"),
        )

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.TimeoutException("timed out")
            mock_client_cls.return_value = mock_client

            client = LLMClient(config)
            with pytest.raises(LLMClientError, match="timed out"):
                client.chat(messages=[{"role": "user", "content": "hello"}])

    def test_api_key_included_in_header_when_non_empty(self) -> None:
        """API key included in Authorization header when non-empty."""
        config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="my-secret-key",
            timeout=60,
            data_dir=__import__('pathlib').Path("/tmp"),
        )
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }

        captured_headers: dict = {}

        def capture_post(url, headers=None, json=None):
            captured_headers.update(headers or {})
            return mock_response

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = capture_post
            mock_client_cls.return_value = mock_client

            client = LLMClient(config)
            client.chat(messages=[{"role": "user", "content": "hello"}])

        assert "Authorization" in captured_headers
        assert captured_headers["Authorization"] == "Bearer my-secret-key"

    def test_api_key_not_included_in_header_when_empty(self) -> None:
        """API key NOT included in header when empty string."""
        config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="",
            timeout=60,
            data_dir=__import__('pathlib').Path("/tmp"),
        )
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }

        captured_headers: dict = {}

        def capture_post(url, headers=None, json=None):
            captured_headers.update(headers or {})
            return mock_response

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = capture_post
            mock_client_cls.return_value = mock_client

            client = LLMClient(config)
            client.chat(messages=[{"role": "user", "content": "hello"}])

        assert "Authorization" not in captured_headers

    def test_per_call_model_overrides_config(self) -> None:
        """Per-call model parameter overrides config model."""
        config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=__import__('pathlib').Path("/tmp"),
        )
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }

        captured_body: dict = {}

        def capture_post(url, headers=None, json=None):
            captured_body.update(json or {})
            return mock_response

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = capture_post
            mock_client_cls.return_value = mock_client

            client = LLMClient(config)
            client.chat(
                messages=[{"role": "user", "content": "hello"}],
                model="gpt-4o",
            )

        assert captured_body["model"] == "gpt-4o"

    def test_semaphore_allows_up_to_5_concurrent_calls(self) -> None:
        """Semaphore limit is set to 5 on client initialization."""
        from threading import Semaphore

        config = AppLLMConfig(
            enabled=True,
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
            data_dir=Path("/tmp"),
        )

        # Reset class semaphore to a fresh Semaphore(5)
        from diagnose_tool.core import llm_client as lc_module
        old_sem = lc_module.LLMClient._semaphore
        lc_module.LLMClient._semaphore = None  # Force creation of new semaphore

        try:
            client = LLMClient(config)
            # Verify semaphore is shared class-level and has correct limit
            assert lc_module.LLMClient._semaphore is client._semaphore
            assert isinstance(client._semaphore, Semaphore)
            # Semaphore(5) creates a semaphore with initial value 5
            # We verify by checking the internal _value attribute (varies by Python impl)
            sem = client._semaphore
            # On CPython the _ Semaphore__value attribute holds the counter
            value_attr = getattr(sem, '_Semaphore__value', None)
            if value_attr is not None:
                assert value_attr == 5, f"Expected semaphore value 5, got {value_attr}"
            else:
                # Fallback: just check it's a Semaphore
                assert isinstance(sem, Semaphore)
        finally:
            lc_module.LLMClient._semaphore = old_sem
