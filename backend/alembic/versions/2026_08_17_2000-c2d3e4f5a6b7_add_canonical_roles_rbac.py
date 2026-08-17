"""add_canonical_roles_rbac

Revision ID: c2d3e4f5a6b7
Revises: f1e2d3c4b5a6
Create Date: 2026-08-17 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'f1e2d3c4b5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_inspector():
    bind = op.get_bind()
    return sa.inspect(bind)


def table_exists(table_name: str, schema: str = None) -> bool:
    inspector = get_inspector()
    return table_name in inspector.get_table_names(schema=schema)


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # In PostgreSQL, native enum types must have the new values added
    if is_postgres:
        for val in ['MENTOR', 'STUDENT']:
            try:
                op.execute(sa.text(f"ALTER TYPE orgrole ADD VALUE IF NOT EXISTS '{val}'"))
            except Exception:
                pass

    # Map any legacy CANDIDATE role records to STUDENT in organization_memberships
    if table_exists('organization_memberships'):
        try:
            op.execute(
                sa.text("UPDATE organization_memberships SET role = 'STUDENT' WHERE role = 'CANDIDATE'")
            )
        except Exception:
            pass

    # Map any legacy CANDIDATE role records to STUDENT in invitations
    if table_exists('invitations'):
        try:
            op.execute(
                sa.text("UPDATE invitations SET role = 'STUDENT' WHERE role = 'CANDIDATE'")
            )
        except Exception:
            pass


def downgrade() -> None:
    # Downgrade reverts STUDENT to CANDIDATE if desired
    if table_exists('organization_memberships'):
        try:
            op.execute(
                sa.text("UPDATE organization_memberships SET role = 'CANDIDATE' WHERE role = 'STUDENT'")
            )
        except Exception:
            pass

    if table_exists('invitations'):
        try:
            op.execute(
                sa.text("UPDATE invitations SET role = 'CANDIDATE' WHERE role = 'STUDENT'")
            )
        except Exception:
            pass
