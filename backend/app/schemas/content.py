import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ContentBase(BaseModel):
    title: str = Field(..., max_length=255)
    master_caption: str
    image_url: str | None = None
    platforms: str = Field(..., pattern=r"^(fb|ig|x|line)(,(fb|ig|x|line))*$")
    publish_at: datetime | None = None
    fb_caption: str | None = None
    ig_caption: str | None = None
    x_caption: str | None = None
    line_message: str | None = None


class ContentCreate(ContentBase):
    pass


class ContentUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    master_caption: str | None = None
    image_url: str | None = None
    platforms: str | None = None
    publish_at: datetime | None = None
    status: str | None = None
    fb_caption: str | None = None
    ig_caption: str | None = None
    x_caption: str | None = None
    line_message: str | None = None


class ContentResponse(ContentBase):
    id: uuid.UUID
    status: str
    retry_count: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduleRequest(BaseModel):
    publish_at: datetime


class PublishLogResponse(BaseModel):
    log_id: uuid.UUID
    content_id: uuid.UUID
    platform: str
    status: str
    external_post_id: str | None
    response_summary: str | None
    workflow_execution_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MonitorDataResponse(BaseModel):
    id: uuid.UUID
    content_id: uuid.UUID
    platform: str
    external_post_id: str | None
    likes: int
    comments: int
    shares: int
    recent_replies: dict | None
    fetched_at: datetime

    model_config = {"from_attributes": True}
