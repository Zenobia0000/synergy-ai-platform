import asyncio
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models.content import ContentQueue

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 30


async def trigger_n8n_publish(content: ContentQueue) -> bool:
    """Call n8n webhook to trigger publishing for a content item."""
    webhook_url = f"{settings.N8N_BASE_URL}/webhook/publish"

    payload = {
        "content_id": str(content.id),
        "title": content.title,
        "master_caption": content.master_caption,
        "image_url": content.image_url,
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


async def check_and_trigger_scheduled() -> int:
    """Check for queued contents past publish_at and trigger publishing."""
    now = datetime.now(timezone.utc)
    triggered = 0

    async with async_session() as db:
        result = await db.execute(
            select(ContentQueue).where(
                ContentQueue.status == "queued",
                ContentQueue.publish_at <= now,
            )
        )
        due_contents = list(result.scalars().all())

        for content in due_contents:
            content.status = "publishing"
            await db.commit()

            success = await trigger_n8n_publish(content)
            if not success:
                content.status = "queued"
                content.last_error = "n8n webhook 呼叫失敗"
                await db.commit()
            else:
                triggered += 1

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
