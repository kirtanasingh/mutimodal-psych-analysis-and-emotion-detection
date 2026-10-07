"""Add video processing statuses and session processing metadata.

Revision ID: 20261006_0004
Revises: 20261006_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20261006_0004"
down_revision: str | None = "20261006_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE session_status ADD VALUE IF NOT EXISTS 'extracting_audio' AFTER 'uploaded'")
    op.execute("ALTER TYPE session_status ADD VALUE IF NOT EXISTS 'extracting_frames' AFTER 'extracting_audio'")
    op.execute("ALTER TYPE session_status ADD VALUE IF NOT EXISTS 'upload_failed' AFTER 'uploaded'")
    op.add_column(
        "sessions",
        sa.Column(
            "processing_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(
                """'{"video_uploaded": false, "audio_extracted": false, "frames_extracted": false, "transcript_generated": false}'::jsonb"""
            ),
        ),
    )
    op.add_column("sessions", sa.Column("processing_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "processing_error")
    op.drop_column("sessions", "processing_steps")
