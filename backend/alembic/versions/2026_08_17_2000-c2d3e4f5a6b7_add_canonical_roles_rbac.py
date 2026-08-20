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

    # In PostgreSQL, native enum types must have the new values added and committed
    # before they can be used in data manipulation (e.g. UPDATE) within SQL queries.
    if is_postgres:
        # Check if orgrole enum exists and what values it contains
        type_exists = bind.execute(
            sa.text("SELECT 1 FROM pg_type WHERE typname = 'orgrole'")
        ).scalar()

        if not type_exists:
            op.execute(
                sa.text("CREATE TYPE orgrole AS ENUM ('ADMIN', 'MENTOR', 'RECRUITER', 'STUDENT', 'COUNSELOR', 'CANDIDATE')")
            )
        else:
            existing_values = [
                row[0]
                for row in bind.execute(
                    sa.text(
                        "SELECT e.enumlabel FROM pg_type t "
                        "JOIN pg_enum e ON t.oid = e.enumtypid "
                        "WHERE t.typname = 'orgrole'"
                    )
                ).fetchall()
            ]
            missing_values = [v for v in ['MENTOR', 'STUDENT'] if v not in existing_values]

            if missing_values:
                # Commit current transaction block so ALTER TYPE ADD VALUE can execute and be immediately usable
                op.execute(sa.text("COMMIT"))
                for val in missing_values:
                    try:
                        op.execute(sa.text(f"ALTER TYPE orgrole ADD VALUE IF NOT EXISTS '{val}'"))
                    except Exception:
                        pass
                op.execute(sa.text("BEGIN"))

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
