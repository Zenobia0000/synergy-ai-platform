import asyncio
import logging
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, update

from app.core.config import settings
from app.core.database import async_session
from app.models.content import ContentQueue
from app.services import storage_service

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 30


async def trigger_n8n_publish(content: ContentQueue) -> bool:
    """Call n8n webhook to trigger publishing for a content item."""
    webhook_url = f"{settings.N8N_BASE_URL}/webhook/publish"

    # Convert relative MinIO upload URLs to absolute (PUBLIC_BASE_URL prefix)
    # so Meta/IG can fetch them via the ngrok tunnel. External URLs
    # (Unsplash etc.) pass through unchanged.
    image_url = storage_service.to_absolute_url(content.image_url)

    payload = {
        "content_id": str(content.id),
        "title": content.title,
        "master_caption": content.master_caption,
        "image_url": image_url,
        "platforms": content.platforms,
        "fb_caption": content.fb_caption,
        "ig_caption": content.ig_caption,
        "x_caption": content.x_caption,
        "line_message": content.line_message,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"X-Webhook-Secret": settings.N8N_WEBHOOK_SECRET},
            )
            if response.status_code in (200, 201, 202):
                logger.info("n8n webhook triggered for content %s", content.id)
                return True
            logger.warning(
                "n8n webhook returned %s for content %s",
                response.status_code,
                content.id,
            )
            return False
    except httpx.RequestError as e:
        logger.error("Failed to call n8n webhook for content %s: %s", content.id, e)
        return False


MAX_RETRY_COUNT = 3


async def _handle_trigger_failure(db, content: ContentQueue) -> None:
    """Shared failure handling: bump retry_count, reset status or mark failed."""
    content.retry_count = (content.retry_count or 0) + 1
    content.last_error = "n8n webhook 呼叫失敗"
    if content.retry_count >= MAX_RETRY_COUNT:
        content.status = "failed"
    else:
        # For immediate publish we reset to draft so the user can retry;
        # for scheduled publish the scheduler re-queues and retries.
        content.status = "draft" if content.publish_at is None else "queued"
    await db.commit()


async def publish_content_now(content_id: uuid.UUID) -> None:
    """Fire-and-forget publish trigger used by the /publish endpoint.

    Opens its own DB session so it can outlive the HTTP request (runs as
    a FastAPI BackgroundTask). Assumes the calling endpoint already set
    status='publishing' and committed.
    """
    async with async_session() as db:
        result = await db.execute(
            select(ContentQueue).where(ContentQueue.id == content_id)
        )
        content = result.scalar_one_or_none()
        if content is None:
            logger.warning("publish_content_now: content %s not found", content_id)
            return

        if content.status != "publishing":
            logger.warning(
                "publish_content_now: content %s in unexpected status %s",
                content_id,
                content.status,
            )
            return

        success = await trigger_n8n_publish(content)
        if not success:
            await _handle_trigger_failure(db, content)


async def check_and_trigger_scheduled() -> int:
    """Atomically claim queued contents past publish_at and trigger publishing.

    Uses a single UPDATE...RETURNING statement so each row can only be
    claimed by one worker, eliminating the SELECT-then-UPDATE race that
    could double-trigger n8n.
    """
    now = datetime.now(timezone.utc)
    triggered = 0

    async with async_session() as db:
        # Atomic claim — each matched row flips queued -> publishing in one
        # statement, so concurrent workers can never claim the same row.
        claim_stmt = (
            update(ContentQueue)
            .where(
                ContentQueue.status == "queued",
                ContentQueue.publish_at <= now,
            )
            .values(status="publishing")
            .returning(ContentQueue)
            .execution_options(synchronize_session=False)
        )
        result = await db.execute(claim_stmt)
        claimed = list(result.scalars().all())
        await db.commit()

        for content in claimed:
            success = await trigger_n8n_publish(content)
            if success:
                triggered += 1
                continue
            await _handle_trigger_failure(db, content)

    return triggered


async def scheduler_loop() -> None:
    """Background loop that checks for scheduled content every interval."""
    logger.info("Scheduler started, checking every %ds", CHECK_INTERVAL_SECONDS)
    while True:
        try:
            count = await check_and_trigger_scheduled()
            if count > 0:
                logger.info("Triggered %d scheduled content(s)", count)
        except Exception:
            logger.exception("Scheduler error")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
