"""Initialize Alembic tracking before application tables are added.

This baseline intentionally creates no FinanceBuddy tables. It establishes the
migration history and verifies a real PostgreSQL connection. The User table and
feature tables will be added in later phases with their own migrations.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Start the migration history; no application tables exist yet."""
    pass


def downgrade() -> None:
    """The baseline has no application objects to remove."""
    pass
