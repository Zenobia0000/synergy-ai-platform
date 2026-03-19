import uuid

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.content import ContentQueue, PublishLog
from app.schemas.response import error_response, success_response
from app.services import content_service

router = APIRouter()


class PublishResultPayload(BaseModel):
    content_id: uuid.UUID
    platform: str
    status: str  # "success" | "failed"
    external_post_id: str | None = None
    response_summary: str | None = None
    workflow_execution_id: str | None = None


@router.post("/publish-result")
async def receive_publish_result(
    payload: PublishResultPayload,
    db: AsyncSession = Depends(get_db),
    x_n8n_signature: str | None = Header(None),
):
    # Webhook signature verification
    if settings.N8N_WEBHOOK_SECRET:
        if x_n8n_signature != settings.N8N_WEBHOOK_SECRET:
            return JSONResponse(
                status_code=401,
                content=error_response(
                    "authentication_error",
                    "webhook_verification_failed",
                    "Webhook 簽名驗證失敗",
                ),
            )

    content = await content_service.get_content(db, payload.content_id)
    if not content:
        return JSONResponse(
            status_code=404,
            content=error_response("not_found", "resource_not_found", "貼文不存在"),
        )

    # Create publish log
    log = PublishLog(
        content_id=payload.content_id,
        platform=payload.platform,
        status=payload.status,
        external_post_id=payload.external_post_id,
        response_summary=payload.response_summary,
        workflow_execution_id=payload.workflow_execution_id,
    )
    db.add(log)

    # Update content status based on all platform results
    await _update_content_status(db, content)

    await db.commit()
    return success_response({"log_id": str(log.log_id)})


async def _update_content_status(db: AsyncSession, content: ContentQueue) -> None:
    """Update content status based on publish logs for all target platforms."""
    from sqlalchemy import select

    result = await db.execute(
        select(PublishLog).where(PublishLog.content_id == content.id)
    )
    logs = list(result.scalars().all())

    target_platforms = set(content.platforms.split(","))
    logged_platforms = {log.platform for log in logs}

    # Not all platforms reported yet
    if not target_platforms.issubset(logged_platforms):
        return

    statuses = {log.platform: log.status for log in logs}
    success_count = sum(1 for s in statuses.values() if s == "success")

    if success_count == len(target_platforms):
        content.status = "success"
    elif success_count > 0:
        content.status = "partial_success"
    else:
        content.status = "failed"
