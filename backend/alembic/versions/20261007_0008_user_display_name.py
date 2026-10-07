"""Add clinician display names."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261007_0008"
down_revision: str | None = "20261007_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=120), nullable=True))
    op.execute("UPDATE users SET display_name = split_part(email, '@', 1) WHERE display_name IS NULL")
    op.alter_column("users", "display_name", nullable=False, server_default="Clinician")


def downgrade() -> None:
    op.drop_column("users", "display_name")
