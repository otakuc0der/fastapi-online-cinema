"""seed user groups

Revision ID: f4ac49a09d9e
Revises: f9a156ad124a
Create Date: 2026-11-05 14:02:53.188958

"""

from enum import Enum
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4ac49a09d9e"
down_revision: Union[str, Sequence[str], None] = "f9a156ad124a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class UserGroupEnum(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


groups_table = sa.table(
    "user_groups",
    sa.column(
        "name",
        sa.Enum(UserGroupEnum, name="usergroupenum"),
    ),
)


def upgrade() -> None:
    """Insert default user groups."""
    op.bulk_insert(
        groups_table,
        [{"name": group} for group in UserGroupEnum],
    )


def downgrade() -> None:
    """Remove default user groups."""
    op.execute(
        groups_table.delete().where(groups_table.c.name.in_(list(UserGroupEnum)))
    )
