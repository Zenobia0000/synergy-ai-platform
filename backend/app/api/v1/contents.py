import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.content import ContentCreate, ContentResponse, ContentUpdate
from app.schemas.response import error_response, paginated_response, success_response
from app.services import content_service

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


@router.delete("/{content_id}", status_code=204)
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
    if content.status != "draft":
        return JSONResponse(
            status_code=403,
            content=error_response(
                "forbidden", "delete_not_allowed", "僅草稿狀態的貼文可刪除"
            ),
        )
    await content_service.delete_content(db, content)


@router.post("/{content_id}/schedule")
async def schedule_content(
    content_id: uuid.UUID,
    data: dict,
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

    publish_at_str = data.get("publish_at")
    if not publish_at_str:
        return JSONResponse(
            status_code=400,
            content=error_response(
                "invalid_request_error", "parameter_missing", "缺少 publish_at", param="publish_at"
            ),
        )

    try:
        publish_at = datetime.fromisoformat(publish_at_str)
    except (ValueError, TypeError):
        return JSONResponse(
            status_code=400,
            content=error_response(
                "invalid_request_error", "parameter_invalid", "publish_at 格式無效", param="publish_at"
            ),
        )

    if publish_at <= datetime.now(timezone.utc):
        return JSONResponse(
            status_code=400,
            content=error_response(
                "invalid_request_error", "invalid_schedule_time", "排程時間必須為未來時間"
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
    return success_response(
        ContentResponse.model_validate(updated).model_dump(mode="json"),
        message="發佈已觸發，請輪詢取得最新狀態",
    )
