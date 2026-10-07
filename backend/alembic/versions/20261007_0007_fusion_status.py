"""Add Phase 8 fusion status and processing step."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261007_0007"
down_revision: str | None = "20261007_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE session_status ADD VALUE IF NOT EXISTS 'fusing'")
    op.alter_column(
        "sessions",
        "processing_steps",
        server_default=sa.text(
            """'{"video_uploaded": false, "audio_extracted": false, "frames_extracted": false, "transcript_generated": false, "emotion_analysis_complete": false, "fusion_complete": false}'::jsonb"""
        ),
    )


def downgrade() -> None:
    op.alter_column("sessions", "processing_steps", server_default=None)
