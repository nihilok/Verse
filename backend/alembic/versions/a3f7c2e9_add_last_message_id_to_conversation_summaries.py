"""add_last_message_id_to_conversation_summaries

Revision ID: a3f7c2e9
Revises: d0d22a6e1dc8
Create Date: 2026-05-17 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f7c2e9"
down_revision: str | Sequence[str] | None = "d0d22a6e1dc8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "conversation_summaries",
        sa.Column("last_message_id", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("conversation_summaries", "last_message_id")
