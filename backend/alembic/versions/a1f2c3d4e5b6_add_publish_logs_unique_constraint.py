"""add unique constraint on publish_logs (content_id, platform)

Revision ID: a1f2c3d4e5b6
Revises: 8b9625b5d0f6
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1f2c3d4e5b6"
down_revision: Union[str, Sequence[str], None] = "8b9625b5d0f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint to prevent duplicate publish logs from
    repeated webhook deliveries (n8n retries) which would otherwise
    inflate per-platform success counts in _update_content_status.
    """
    op.create_unique_constraint(
        "uq_publish_logs_content_platform",
        "publish_logs",
        ["content_id", "platform"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_publish_logs_content_platform",
        "publish_logs",
        type_="unique",
    )
