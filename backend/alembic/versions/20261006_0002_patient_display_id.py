"""Ensure patient display IDs are unique per psychologist.

Revision ID: 20261006_0002
Revises: 20261006_0001
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20261006_0002"
down_revision: str | None = "20261006_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_patients_psychologist_display_id",
        "patients",
        ["psychologist_id", "display_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_patients_psychologist_display_id", "patients", type_="unique")
