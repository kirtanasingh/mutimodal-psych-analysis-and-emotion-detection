"""Add Phase 7 emotion-analysis statuses and processing step."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261007_0006"
down_revision: str | None = "20261006_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE session_status ADD VALUE IF NOT EXISTS 'analyzing_emotions'")
    op.execute("ALTER TYPE session_status ADD VALUE IF NOT EXISTS 'fusion_pending'")
    op.alter_column(
        "sessions",
        "processing_steps",
        server_default=sa.text(
            """'{"video_uploaded": false, "audio_extracted": false, "frames_extracted": false, "transcript_generated": false, "emotion_analysis_complete": false}'::jsonb"""
        ),
    )


def downgrade() -> None:
    op.alter_column("sessions", "processing_steps", server_default=None)
