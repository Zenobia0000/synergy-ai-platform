import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentQueue
from app.schemas.content import ContentCreate, ContentUpdate


async def create_content(db: AsyncSession, data: ContentCreate) -> ContentQueue:
    content = ContentQueue(**data.model_dump())
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return content


async def get_content(db: AsyncSession, content_id: uuid.UUID) -> ContentQueue | None:
    result = await db.execute(
        select(ContentQueue).where(ContentQueue.id == content_id)
    )
    return result.scalar_one_or_none()


async def list_contents(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    sort_by: str = "-created_at",
) -> tuple[list[ContentQueue], int]:
    query = select(ContentQueue)
    count_query = select(func.count()).select_from(ContentQueue)

    if status:
        query = query.where(ContentQueue.status == status)
        count_query = count_query.where(ContentQueue.status == status)

    # Sorting
    desc = sort_by.startswith("-")
    field_name = sort_by.lstrip("-")
    column = getattr(ContentQueue, field_name, ContentQueue.created_at)
    query = query.order_by(column.desc() if desc else column.asc())

    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    items = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return items, total


async def update_content(
    db: AsyncSession, content: ContentQueue, data: ContentUpdate
) -> ContentQueue:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
    await db.commit()
    await db.refresh(content)
    return content


async def delete_content(db: AsyncSession, content: ContentQueue) -> None:
    await db.delete(content)
    await db.commit()


async def schedule_content(
    db: AsyncSession, content: ContentQueue, publish_at: datetime
) -> ContentQueue:
    content.publish_at = publish_at
    content.status = "queued"
    await db.commit()
    await db.refresh(content)
    return content


async def cancel_schedule(db: AsyncSession, content: ContentQueue) -> ContentQueue:
    content.publish_at = None
    content.status = "draft"
    await db.commit()
    await db.refresh(content)
    return content


async def set_publishing(db: AsyncSession, content: ContentQueue) -> ContentQueue:
    content.status = "publishing"
    if not content.publish_at:
        content.publish_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(content)
    return content
