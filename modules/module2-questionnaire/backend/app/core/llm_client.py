"""LLM Client — thin wrapper around litellm.

Provides:
- Unified async interface (complete_json / complete_text)
- Exponential-backoff retry for transient errors (no extra deps)
- Token-usage logging (no API key leakage)
- PII masking in log output
- Custom exception hierarchy
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

import litellm

from app.core.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry configuration
# ---------------------------------------------------------------------------

_MAX_RETRIES = 3
_BASE_DELAY_SECONDS = 1.0  # exponential: 1s, 2s, 4s


# ---------------------------------------------------------------------------
# PII helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# Taiwan mobile: 09xx-xxx-xxx  or  09xxxxxxxxx (10 digits starting with 09)
_TW_MOBILE_RE = re.compile(r"09\d{2}[-\s]?\d{3}[-\s]?\d{3}")

# Markdown fence patterns some LLMs wrap JSON output in.
_JSON_FENCE_RE = re.compile(
    r"^\s*```(?:json)?\s*(?P<body>.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE
)


def _mask_pii(text: str) -> str:
    """Replace known PII patterns (email, Taiwan mobile) with '***'."""
    text = _EMAIL_RE.sub("***", text)
    text = _TW_MOBILE_RE.sub("***", text)
    return text


def _extract_json_payload(raw: str) -> str:
    """Best-effort cleanup for LLM outputs that wrap JSON in markdown or prose.

    Handles:
    - ```json ... ``` fences
    - Leading/trailing prose around a JSON object/array
    - Common escape-character confusion (literal backslash-n instead of real newline)

    Returns the most likely JSON substring. Does NOT guarantee validity —
    callers must still try json.loads and handle failures.
    """
    if raw is None:
        return ""
    s = raw.strip()
    if not s:
        return s

    # 1. Strip markdown code fences.
    m = _JSON_FENCE_RE.match(s)
    if m:
        s = m.group("body").strip()

    # 2. If still not starting with { or [, find the first JSON-looking character.
    if s and s[0] not in "{[":
        obj_start = s.find("{")
        arr_start = s.find("[")
        candidates = [i for i in (obj_start, arr_start) if i >= 0]
        if candidates:
            s = s[min(candidates):]

    # 3. Trim trailing prose after the matching closing bracket.
    if s and s[0] in "{[":
        open_ch, close_ch = ("{", "}") if s[0] == "{" else ("[", "]")
        depth = 0
        in_string = False
        escape = False
        end_idx = -1
        for i, ch in enumerate(s):
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break
        if end_idx >= 0:
            s = s[: end_idx + 1]

    return s


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class LLMError(Exception):
    """Base exception for all LLM-related errors."""


class LLMTimeoutError(LLMError):
    """Raised when the LLM call times out after all retries."""


class LLMJSONError(LLMError):
    """Raised when the LLM response cannot be parsed as JSON."""


class LLMRateLimitError(LLMError):
    """Raised when the LLM provider returns a rate-limit error."""


# ---------------------------------------------------------------------------
# Retryable error detection
# ---------------------------------------------------------------------------

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    """Return True for transient errors that should be retried."""
    if isinstance(exc, TimeoutError):
        return True
    # litellm wraps HTTP errors in various exception types; check status code
    status_code: int | None = getattr(exc, "status_code", None)
    if status_code in _RETRYABLE_STATUS_CODES:
        return True
    # Rate-limit signal from litellm
    if "rate limit" in str(exc).lower() or "ratelimit" in str(exc).lower():
        return True
    return False


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------


class LLMClient:
    """Async wrapper around litellm.acompletion.

    Parameters
    ----------
    settings:
        Application settings (injected; not fetched inside to keep testable).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        response_schema: dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Call LLM and parse the response as JSON.

        Parameters
        ----------
        system:
            System prompt.
        user:
            User message.
        response_schema:
            Optional JSON Schema dict forwarded as guidance (not enforced by all providers).
        model:
            Override the default model (e.g. ``"openai/gpt-4o"``).
        temperature:
            Override temperature.
        max_tokens:
            Override max_tokens.

        Returns
        -------
        dict[str, Any]
            Parsed JSON object from the LLM response.

        Raises
        ------
        LLMJSONError
            If the response cannot be parsed as JSON (no retry).
        LLMTimeoutError
            If all retry attempts timed out.
        LLMRateLimitError
            If the provider signals a rate-limit error after all retries.
        LLMError
            For other LLM-level errors.
        """
        raw = await self._call_with_retry(
            system=system,
            user=user,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        cleaned = _extract_json_payload(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            # Log the full raw content (PII-masked) so we can diagnose
            # whether the issue is truncation, extra prose, or escape confusion.
            logger.error(
                "LLM JSON parse failed | raw_length=%d | cleaned_length=%d | raw=%s",
                len(raw) if raw else 0,
                len(cleaned) if cleaned else 0,
                _mask_pii(raw or "")[:2000],
            )
            # Give the error path a usable excerpt — tail often shows why it broke.
            preview_head = cleaned[:200]
            preview_tail = cleaned[-200:] if len(cleaned) > 400 else ""
            raise LLMJSONError(
                "LLM returned non-JSON content "
                f"(len={len(cleaned)}): head={preview_head!r} tail={preview_tail!r}"
            ) from exc

    async def complete_text(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **_kwargs: Any,
    ) -> str:
        """Plain-text completion.

        Returns
        -------
        str
            Stripped text content from the LLM response.
        """
        raw = await self._call_with_retry(
            system=system,
            user=user,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return raw.strip()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_with_retry(
        self,
        *,
        system: str,
        user: str,
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
        **extra_kwargs: Any,
    ) -> str:
        """Execute litellm.acompletion with exponential-backoff retry.

        Only retries transient errors (timeout, 5xx, rate-limit).
        JSON parse errors are NOT retried.
        """
        effective_model = model or self._settings.litellm_model
        effective_temperature = temperature if temperature is not None else self._settings.llm_temperature
        effective_max_tokens = max_tokens if max_tokens is not None else self._settings.llm_max_tokens

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        last_exc: BaseException | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = await litellm.acompletion(
                    model=effective_model,
                    messages=messages,
                    temperature=effective_temperature,
                    max_tokens=effective_max_tokens,
                    timeout=self._settings.llm_timeout_seconds,
                    **extra_kwargs,
                )
                self._log_usage(response, effective_model)
                content: str = response["choices"][0]["message"]["content"]
                return content
            except BaseException as exc:
                last_exc = exc
                if not _is_retryable(exc):
                    raise
                if attempt < _MAX_RETRIES - 1:
                    delay = _BASE_DELAY_SECONDS * (2 ** attempt)
                    logger.warning(
                        "LLM call failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                        type(exc).__name__,
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted — wrap in appropriate exception type
        assert last_exc is not None
        if isinstance(last_exc, TimeoutError):
            raise LLMTimeoutError("LLM timed out after all retries") from last_exc
        status_code: int | None = getattr(last_exc, "status_code", None)
        if status_code == 429 or "rate limit" in str(last_exc).lower():
            raise LLMRateLimitError("LLM rate-limit exceeded after all retries") from last_exc
        raise LLMError("LLM error after all retries") from last_exc

    def _log_usage(self, response: Any, model: str) -> None:
        """Log token usage without leaking API keys or PII."""
        usage = response.get("usage", {}) if isinstance(response, dict) else {}
        prompt_tokens = usage.get("prompt_tokens", "?")
        completion_tokens = usage.get("completion_tokens", "?")
        logger.debug(
            "LLM usage | model=%s prompt_tokens=%s completion_tokens=%s",
            model,
            prompt_tokens,
            completion_tokens,
        )
