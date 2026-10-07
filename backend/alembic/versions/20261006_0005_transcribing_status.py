"""Add the transcription processing status.

Revision ID: 20261006_0005
Revises: 20261006_0004
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20261006_0005"
down_revision: str | None = "20261006_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE session_status ADD VALUE IF NOT EXISTS 'transcribing' AFTER 'extracting_frames'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass
