"""Tests for app.core.config — Settings and get_settings."""

import pytest


class TestSettingsDefaults:
    """Verify default values without any env overrides."""

    def test_default_litellm_model(self) -> None:
        from app.core.config import Settings

        s = Settings()
        assert s.litellm_model == "gemini/gemini-2.5-flash"

    def test_default_temperature(self) -> None:
        from app.core.config import Settings

        s = Settings()
        assert s.llm_temperature == pytest.approx(0.3)

    def test_default_max_tokens(self) -> None:
        from app.core.config import Settings

        s = Settings()
        assert s.llm_max_tokens == 16384

    def test_default_timeout(self) -> None:
        from app.core.config import Settings

        s = Settings()
        assert s.llm_timeout_seconds == pytest.approx(30.0)

    def test_default_app_env(self) -> None:
        from app.core.config import Settings

        s = Settings()
        assert s.app_env == "dev"

    def test_default_log_level(self) -> None:
        from app.core.config import Settings

        s = Settings()
        assert s.log_level == "INFO"

    def test_gemini_api_key_defaults_to_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """API key should default to empty string so tests can run without real key.

        Clear env + .env so the assertion is not polluted by a developer's real key.
        """
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        # Bypass .env file loading for this default-value test.
        from app.core.config import Settings

        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.gemini_api_key == ""


class TestSettingsEnvOverride:
    """Verify env vars are correctly picked up."""

    def test_litellm_model_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LITELLM_MODEL", "gemini/gemini-2.5-pro")
        from app.core.config import Settings

        s = Settings()
        assert s.litellm_model == "gemini/gemini-2.5-pro"

    def test_temperature_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_TEMPERATURE", "0.7")
        from app.core.config import Settings

        s = Settings()
        assert s.llm_temperature == pytest.approx(0.7)

    def test_extra_env_does_not_raise(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """extra='ignore' — unknown env vars should be silently dropped."""
        monkeypatch.setenv("TOTALLY_UNKNOWN_VAR", "surprise")
        from app.core.config import Settings

        # Should not raise ValidationError
        s = Settings()
        assert s is not None

    def test_gemini_api_key_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-abc")
        from app.core.config import Settings

        s = Settings()
        assert s.gemini_api_key == "test-key-abc"


class TestGetSettings:
    """Verify get_settings caching behaviour."""

    def test_get_settings_returns_settings_instance(self) -> None:
        from app.core.config import Settings, get_settings

        result = get_settings()
        assert isinstance(result, Settings)

    def test_get_settings_returns_same_instance(self) -> None:
        """lru_cache ensures the same object is returned on repeated calls."""
        from app.core.config import get_settings

        a = get_settings()
        b = get_settings()
        assert a is b
