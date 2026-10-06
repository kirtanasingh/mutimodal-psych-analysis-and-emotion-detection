"""Add the created session status for the Phase 4 upload lifecycle.

Revision ID: 20261006_0003
Revises: 20261006_0002
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20261006_0003"
down_revision: str | None = "20261006_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE session_status ADD VALUE IF NOT EXISTS 'created' BEFORE 'uploaded'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass
