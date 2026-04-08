import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Content Distributor API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database — must be provided via env in non-test environments
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/content_distributor"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"]

    # n8n
    N8N_BASE_URL: str = "http://localhost:5678"
    N8N_WEBHOOK_SECRET: str = ""

    # Auth (預留)
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # MinIO object storage (S3-compatible)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_BUCKET: str = "content-images"
    MINIO_SECURE: bool = False  # http inside docker network

    # Public base URL — used to build image URLs that Instagram/Meta can fetch.
    # Set to an ngrok / cloudflared tunnel URL during local dev.
    # Leave blank for tests; backend falls back to relative URLs.
    PUBLIC_BASE_URL: str = ""

    # Test mode flag — set by test fixtures to relax startup validation
    TESTING: bool = False

    model_config = {"env_file": ".env", "case_sensitive": True}

    def validate_runtime(self) -> None:
        """Fail-fast validation of secrets that must not use insecure defaults.

        Skipped when TESTING=True (set by pytest fixtures).
        """
        if self.TESTING:
            return
        if not self.N8N_WEBHOOK_SECRET:
            raise RuntimeError(
                "N8N_WEBHOOK_SECRET is not set. Refusing to start: an empty secret "
                "would let any caller invoke /webhooks endpoints."
            )
        if self.SECRET_KEY in ("", "change-me-in-production"):
            raise RuntimeError(
                "SECRET_KEY must be set to a non-default value via environment."
            )


settings = Settings()

# Allow tests to opt-out of runtime validation via env var
if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING") == "1":
    settings.TESTING = True
