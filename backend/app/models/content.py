import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContentQueue(Base):
    __tablename__ = "content_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    master_caption: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    platforms: Mapped[str] = mapped_column(String(100))  # "fb,ig,x,line"
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # Platform-specific captions
    fb_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    ig_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    x_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    publish_logs: Mapped[list["PublishLog"]] = relationship(back_populates="content", cascade="all, delete-orphan")
    monitor_data: Mapped[list["MonitorData"]] = relationship(back_populates="content", cascade="all, delete-orphan")


class PublishLog(Base):
    __tablename__ = "publish_logs"
    __table_args__ = (
        UniqueConstraint(
            "content_id",
            "platform",
            name="uq_publish_logs_content_platform",
        ),
    )

    log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_queue.id"))
    platform: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_execution_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    content: Mapped["ContentQueue"] = relationship(back_populates="publish_logs")


class MonitorData(Base):
    __tablename__ = "monitor_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_queue.id"))
    platform: Mapped[str] = mapped_column(String(20))
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    recent_replies: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    content: Mapped["ContentQueue"] = relationship(back_populates="monitor_data")
