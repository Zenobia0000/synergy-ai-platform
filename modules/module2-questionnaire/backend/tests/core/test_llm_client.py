"""Tests for app.core.llm_client — LLMClient and helpers.

All tests mock litellm.acompletion so no real API key is required.
"""

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(content: str, prompt_tokens: int = 10, completion_tokens: int = 5) -> dict[str, Any]:
    """Build a minimal litellm-style response dict."""
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
        "model": "gemini/gemini-2.5-flash",
    }


def _make_settings(model: str = "gemini/gemini-2.5-flash") -> Any:
    from app.core.config import Settings

    return Settings(
        gemini_api_key="test-key",
        litellm_model=model,
        llm_temperature=0.3,
        llm_max_tokens=2048,
        llm_timeout_seconds=30.0,
    )


# ---------------------------------------------------------------------------
# complete_json
# ---------------------------------------------------------------------------

class TestCompleteJson:
    async def test_complete_json_returns_parsed_dict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.llm_client import LLMClient

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            return _make_response('{"ok": true, "score": 42}')

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        client = LLMClient(_make_settings())
        result = await client.complete_json(system="sys", user="usr")
        assert result == {"ok": True, "score": 42}

    async def test_complete_json_raises_on_invalid_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.llm_client import LLMClient, LLMJSONError

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            return _make_response("This is NOT json at all")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        client = LLMClient(_make_settings())
        with pytest.raises(LLMJSONError):
            await client.complete_json(system="sys", user="usr")

    async def test_complete_json_passes_response_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify json_object response_format is forwarded to litellm."""
        captured: dict[str, Any] = {}

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return _make_response('{"x": 1}')

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        from app.core.llm_client import LLMClient

        client = LLMClient(_make_settings())
        await client.complete_json(system="sys", user="usr")
        assert captured.get("response_format") == {"type": "json_object"}


# ---------------------------------------------------------------------------
# complete_text
# ---------------------------------------------------------------------------

class TestCompleteText:
    async def test_complete_text_returns_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.llm_client import LLMClient

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            return _make_response("Hello world")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        client = LLMClient(_make_settings())
        result = await client.complete_text(system="sys", user="usr")
        assert result == "Hello world"

    async def test_complete_text_strips_whitespace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.llm_client import LLMClient

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            return _make_response("  trimmed  \n")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        client = LLMClient(_make_settings())
        result = await client.complete_text(system="sys", user="usr")
        assert result == "trimmed"


# ---------------------------------------------------------------------------
# PII masking
# ---------------------------------------------------------------------------

class TestMaskPii:
    def test_mask_pii_redacts_email(self) -> None:
        from app.core.llm_client import _mask_pii

        result = _mask_pii("Contact me at user@example.com for more info.")
        assert "user@example.com" not in result
        assert "***" in result or "[REDACTED]" in result

    def test_mask_pii_redacts_taiwan_mobile(self) -> None:
        """Taiwan mobile: 09xx-xxx-xxx or 09xxxxxxxx."""
        from app.core.llm_client import _mask_pii

        result = _mask_pii("My phone is 0912-345-678.")
        assert "0912-345-678" not in result
        assert "***" in result or "[REDACTED]" in result

    def test_mask_pii_redacts_taiwan_mobile_no_dash(self) -> None:
        from app.core.llm_client import _mask_pii

        result = _mask_pii("Call me at 0987654321 anytime.")
        assert "0987654321" not in result

    def test_mask_pii_leaves_non_pii_intact(self) -> None:
        from app.core.llm_client import _mask_pii

        text = "Please answer the following questionnaire."
        result = _mask_pii(text)
        assert result == text


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

class TestRetry:
    async def test_retry_on_timeout_then_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """First call raises TimeoutError; second call succeeds."""
        from app.core.llm_client import LLMClient

        call_count = 0

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("simulated timeout")
            return _make_response("hello")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        # Patch asyncio.sleep to avoid actual waiting in tests
        monkeypatch.setattr("app.core.llm_client.asyncio.sleep", AsyncMock())

        client = LLMClient(_make_settings())
        result = await client.complete_text(system="sys", user="usr")
        assert result == "hello"
        assert call_count == 2

    async def test_retry_max_attempts_then_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """After max retries, the original exception should propagate."""
        from app.core.llm_client import LLMClient, LLMTimeoutError

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            raise TimeoutError("always fails")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        monkeypatch.setattr("app.core.llm_client.asyncio.sleep", AsyncMock())

        client = LLMClient(_make_settings())
        with pytest.raises(LLMTimeoutError):
            await client.complete_text(system="sys", user="usr")

    async def test_no_retry_on_json_parse_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """JSON parse errors should not trigger retry — they are client errors."""
        from app.core.llm_client import LLMClient, LLMJSONError

        call_count = 0

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return _make_response("not json")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        monkeypatch.setattr("app.core.llm_client.asyncio.sleep", AsyncMock())

        client = LLMClient(_make_settings())
        with pytest.raises(LLMJSONError):
            await client.complete_json(system="sys", user="usr")
        # Should only call once — no retry for JSON errors
        assert call_count == 1


# ---------------------------------------------------------------------------
# Model override
# ---------------------------------------------------------------------------

class TestModelOverride:
    async def test_model_override_is_used(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Passing model= kwarg should forward the override to litellm."""
        from app.core.llm_client import LLMClient

        captured: dict[str, Any] = {}

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return _make_response("hello")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        client = LLMClient(_make_settings())
        await client.complete_text(system="sys", user="usr", model="openai/gpt-4o")
        assert captured["model"] == "openai/gpt-4o"

    async def test_default_model_from_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without override, the model from Settings should be used."""
        from app.core.llm_client import LLMClient

        captured: dict[str, Any] = {}

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return _make_response("hello")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        client = LLMClient(_make_settings(model="gemini/gemini-2.5-flash"))
        await client.complete_text(system="sys", user="usr")
        assert captured["model"] == "gemini/gemini-2.5-flash"


# ---------------------------------------------------------------------------
# Token logging
# ---------------------------------------------------------------------------

class TestTokenLogging:
    async def test_logs_token_usage(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        from app.core.llm_client import LLMClient

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            return _make_response("hello", prompt_tokens=15, completion_tokens=8)

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        client = LLMClient(_make_settings())

        with caplog.at_level(logging.DEBUG, logger="app.core.llm_client"):
            await client.complete_text(system="sys", user="usr")

        log_text = " ".join(caplog.messages)
        assert "15" in log_text or "prompt" in log_text.lower()
        assert "8" in log_text or "completion" in log_text.lower()

    async def test_api_key_not_logged(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        from app.core.llm_client import LLMClient

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            return _make_response("hello")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        client = LLMClient(_make_settings())

        with caplog.at_level(logging.DEBUG, logger="app.core.llm_client"):
            await client.complete_text(system="sys", user="test prompt")

        log_text = " ".join(caplog.messages)
        assert "test-key" not in log_text


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_llm_timeout_error_is_llm_error(self) -> None:
        from app.core.llm_client import LLMError, LLMTimeoutError

        assert issubclass(LLMTimeoutError, LLMError)

    def test_llm_json_error_is_llm_error(self) -> None:
        from app.core.llm_client import LLMError, LLMJSONError

        assert issubclass(LLMJSONError, LLMError)

    def test_llm_rate_limit_error_is_llm_error(self) -> None:
        from app.core.llm_client import LLMError, LLMRateLimitError

        assert issubclass(LLMRateLimitError, LLMError)


# ---------------------------------------------------------------------------
# _is_retryable — status_code and rate-limit string detection
# ---------------------------------------------------------------------------

class TestIsRetryable:
    def test_retryable_status_code_429(self) -> None:
        from app.core.llm_client import _is_retryable

        exc = Exception("rate limited")
        exc.status_code = 429  # type: ignore[attr-defined]
        assert _is_retryable(exc) is True

    def test_retryable_status_code_503(self) -> None:
        from app.core.llm_client import _is_retryable

        exc = Exception("service unavailable")
        exc.status_code = 503  # type: ignore[attr-defined]
        assert _is_retryable(exc) is True

    def test_retryable_rate_limit_in_message(self) -> None:
        from app.core.llm_client import _is_retryable

        exc = Exception("You have hit the rate limit for this model")
        assert _is_retryable(exc) is True

    def test_retryable_ratelimit_in_message(self) -> None:
        from app.core.llm_client import _is_retryable

        exc = Exception("RateLimit exceeded")
        assert _is_retryable(exc) is True

    def test_not_retryable_value_error(self) -> None:
        from app.core.llm_client import _is_retryable

        exc = ValueError("bad input")
        assert _is_retryable(exc) is False

    def test_not_retryable_status_code_400(self) -> None:
        from app.core.llm_client import _is_retryable

        exc = Exception("bad request")
        exc.status_code = 400  # type: ignore[attr-defined]
        assert _is_retryable(exc) is False


# ---------------------------------------------------------------------------
# Retry exhaustion — rate-limit and generic error wrapping
# ---------------------------------------------------------------------------

class TestRetryExhaustion:
    async def test_rate_limit_error_after_all_retries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All retries fail with rate-limit signal → LLMRateLimitError."""
        from app.core.llm_client import LLMClient, LLMRateLimitError

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            exc = Exception("rate limit exceeded")
            exc.status_code = 429  # type: ignore[attr-defined]
            raise exc

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        monkeypatch.setattr("app.core.llm_client.asyncio.sleep", AsyncMock())

        client = LLMClient(_make_settings())
        with pytest.raises(LLMRateLimitError):
            await client.complete_text(system="sys", user="usr")

    async def test_generic_llm_error_after_all_retries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All retries fail with a 502 → wraps as generic LLMError."""
        from app.core.llm_client import LLMClient, LLMError

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            exc = Exception("bad gateway")
            exc.status_code = 502  # type: ignore[attr-defined]
            raise exc

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        monkeypatch.setattr("app.core.llm_client.asyncio.sleep", AsyncMock())

        client = LLMClient(_make_settings())
        with pytest.raises(LLMError):
            await client.complete_text(system="sys", user="usr")

    async def test_non_retryable_error_raises_immediately(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-retryable error (ValueError) must raise on first attempt without retrying."""
        from app.core.llm_client import LLMClient

        call_count = 0

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            raise ValueError("bad input — not retryable")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        monkeypatch.setattr("app.core.llm_client.asyncio.sleep", AsyncMock())

        client = LLMClient(_make_settings())
        with pytest.raises(ValueError):
            await client.complete_text(system="sys", user="usr")
        assert call_count == 1  # no retry

    async def test_rate_limit_string_in_message_raises_rate_limit_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """rate limit in exception message (no status_code) → LLMRateLimitError after retries."""
        from app.core.llm_client import LLMClient, LLMRateLimitError

        async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
            raise Exception("rate limit exceeded for your plan")

        monkeypatch.setattr("app.core.llm_client.litellm.acompletion", fake_acompletion)
        monkeypatch.setattr("app.core.llm_client.asyncio.sleep", AsyncMock())

        client = LLMClient(_make_settings())
        with pytest.raises(LLMRateLimitError):
            await client.complete_text(system="sys", user="usr")
