import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.content import (
    ContentCreate,
    ContentResponse,
    ContentUpdate,
    ScheduleRequest,
)
from app.schemas.response import error_response, paginated_response, success_response
from app.services import content_service
from app.services.scheduler_service import publish_content_now

router = APIRouter()


@router.post("", status_code=201)
async def create_content(
    data: ContentCreate,
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.create_content(db, data)
    return success_response(ContentResponse.model_validate(content).model_dump(mode="json"))


@router.get("")
async def list_contents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    sort_by: str = Query("-created_at"),
    db: AsyncSession = Depends(get_db),
):
    items, total = await content_service.list_contents(db, page, limit, status, sort_by)
    data = [ContentResponse.model_validate(item).model_dump(mode="json") for item in items]
    return paginated_response(data, total, page, limit)


@router.get("/{content_id}")
async def get_content(
    content_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.get_content(db, content_id)
    if not content:
        return JSONResponse(
            status_code=404,
            content=error_response("not_found", "resource_not_found", "貼文不存在"),
        )
    return success_response(ContentResponse.model_validate(content).model_dump(mode="json"))


@router.put("/{content_id}")
async def update_content(
    content_id: uuid.UUID,
    data: ContentUpdate,
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.get_content(db, content_id)
    if not content:
        return JSONResponse(
            status_code=404,
            content=error_response("not_found", "resource_not_found", "貼文不存在"),
        )
    updated = await content_service.update_content(db, content, data)
    return success_response(ContentResponse.model_validate(updated).model_dump(mode="json"))


DELETABLE_STATUSES = {"draft", "failed"}


@router.delete("/{content_id}")
async def delete_content(
    content_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.get_content(db, content_id)
    if not content:
        return JSONResponse(
            status_code=404,
            content=error_response("not_found", "resource_not_found", "貼文不存在"),
        )
    if content.status not in DELETABLE_STATUSES:
        return JSONResponse(
            status_code=403,
            content=error_response(
                "forbidden",
                "delete_not_allowed",
                f"狀態 {content.status} 的貼文無法刪除（僅草稿與失敗可刪）",
            ),
        )
    await content_service.delete_content(db, content)
    # Only the success path returns 204 — error paths above are JSON bodies
    # with their own status codes.
    return Response(status_code=204)


@router.post("/{content_id}/schedule")
async def schedule_content(
    content_id: uuid.UUID,
    data: ScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.get_content(db, content_id)
    if not content:
        return JSONResponse(
            status_code=404,
            content=error_response("not_found", "resource_not_found", "貼文不存在"),
        )
    if content.status != "draft":
        return JSONResponse(
            status_code=409,
            content=error_response(
                "conflict", "invalid_status_transition", "僅草稿狀態可設定排程"
            ),
        )

    publish_at = data.publish_at
    # Normalize naive datetimes to UTC so the comparison is unambiguous.
    if publish_at.tzinfo is None:
        publish_at = publish_at.replace(tzinfo=timezone.utc)

    if publish_at <= datetime.now(timezone.utc):
        return JSONResponse(
            status_code=400,
            content=error_response(
                "invalid_request_error",
                "invalid_schedule_time",
                "排程時間必須為未來時間",
                param="publish_at",
            ),
        )

    updated = await content_service.schedule_content(db, content, publish_at)
    return success_response(ContentResponse.model_validate(updated).model_dump(mode="json"))


@router.delete("/{content_id}/schedule")
async def cancel_schedule(
    content_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.get_content(db, content_id)
    if not content:
        return JSONResponse(
            status_code=404,
            content=error_response("not_found", "resource_not_found", "貼文不存在"),
        )
    if content.status != "queued":
        return JSONResponse(
            status_code=409,
            content=error_response(
                "conflict", "invalid_status_transition", "僅已排程狀態可取消排程"
            ),
        )
    updated = await content_service.cancel_schedule(db, content)
    return success_response(ContentResponse.model_validate(updated).model_dump(mode="json"))


@router.post("/{content_id}/publish", status_code=202)
async def publish_content(
    content_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.get_content(db, content_id)
    if not content:
        return JSONResponse(
            status_code=404,
            content=error_response("not_found", "resource_not_found", "貼文不存在"),
        )
    if content.status not in ("draft", "queued"):
        return JSONResponse(
            status_code=409,
            content=error_response(
                "conflict", "invalid_status_transition",
                f"狀態 {content.status} 無法發佈，僅 draft/queued 可發佈"
            ),
        )
    updated = await content_service.set_publishing(db, content)
    # Fire-and-forget trigger to n8n after the response is sent. We use
    # BackgroundTasks so the HTTP request returns immediately (202) and
    # the user gets instant feedback; status is updated asynchronously
    # by the webhook callback when n8n finishes publishing.
    background_tasks.add_task(publish_content_now, content_id)
    return success_response(
        ContentResponse.model_validate(updated).model_dump(mode="json"),
        message="發佈已觸發，請輪詢取得最新狀態",
    )
