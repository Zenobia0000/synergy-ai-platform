"""MinIO / S3-compatible object storage wrapper.

Uses the synchronous `minio` SDK wrapped in `asyncio.to_thread` for async
compatibility. Single-user MVP scale — fine for dev/MVP, swap to aioboto3
or true async client later if throughput becomes a concern.
"""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Iterator

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)

# Single shared client. Created lazily so test environments without MinIO
# don't pay the connection cost on import.
_client: Minio | None = None


def _get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )
    return _client


async def ensure_bucket() -> None:
    """Idempotently create the bucket if it doesn't exist.

    Called on app startup. The minio-init container also creates it
    via mc, but doing it here makes the backend self-sufficient if
    someone runs MinIO standalone.
    """
    def _sync() -> None:
        client = _get_client()
        if not client.bucket_exists(settings.MINIO_BUCKET):
            client.make_bucket(settings.MINIO_BUCKET)
            logger.info("Created MinIO bucket: %s", settings.MINIO_BUCKET)

    try:
        await asyncio.to_thread(_sync)
    except S3Error as e:
        logger.warning("MinIO ensure_bucket failed: %s", e)


async def put_object(
    key: str,
    data: bytes,
    content_type: str,
) -> None:
    """Upload a binary blob to MinIO under the given key."""
    def _sync() -> None:
        client = _get_client()
        client.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=key,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    await asyncio.to_thread(_sync)


async def stat_object(key: str) -> tuple[int, str]:
    """Return (size, content_type) for an object, or raise S3Error."""
    def _sync() -> tuple[int, str]:
        client = _get_client()
        stat = client.stat_object(settings.MINIO_BUCKET, key)
        return stat.size, stat.content_type or "application/octet-stream"

    return await asyncio.to_thread(_sync)


def get_object_stream(key: str) -> Iterator[bytes]:
    """Return a streaming iterator for an object's bytes.

    Synchronous on purpose — FastAPI's StreamingResponse handles the
    async wrapping. The minio SDK's `get_object` returns an
    `urllib3.HTTPResponse` which is a file-like iterator.

    Caller is responsible for closing the response (use try/finally
    or context manager).
    """
    client = _get_client()
    return client.get_object(settings.MINIO_BUCKET, key)


def build_relative_url(key: str) -> str:
    """Return the backend proxy path for an uploaded image.

    Always returns a relative URL like `/api/v1/uploads/{key}`. This is
    what gets stored in the DB and rendered by the frontend (the vite
    dev proxy forwards `/api/*` to the backend, so browser can load
    images without going through any tunnel).
    """
    return f"/api/v1/uploads/{key}"


def to_absolute_url(url: str | None) -> str | None:
    """Convert a relative upload URL to an absolute one Instagram can fetch.

    Used at the moment we send the payload to n8n: if `image_url` is
    relative (i.e. begins with `/`), prepend `PUBLIC_BASE_URL` (the
    ngrok / cloudflared tunnel). Already-absolute URLs (e.g. user
    pasted an Unsplash link) pass through unchanged.
    """
    if not url:
        return url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if not settings.PUBLIC_BASE_URL:
        # Tunnel not configured — IG won't be able to fetch but we
        # leave the path alone so callers can detect this in tests.
        return url
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    return f"{base}{url}"
