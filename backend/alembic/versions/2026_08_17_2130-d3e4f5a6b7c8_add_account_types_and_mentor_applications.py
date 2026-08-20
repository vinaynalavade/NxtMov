"""add_account_types_and_mentor_applications

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-08-17 21:30:00.000000

"""
from typing import Sequence, Union
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_inspector():
    bind = op.get_bind()
    return sa.inspect(bind)


def table_exists(table_name: str, schema: str = None) -> bool:
    inspector = get_inspector()
    return table_name in inspector.get_table_names(schema=schema)


def column_exists(table_name: str, column_name: str, schema: str = None) -> bool:
    inspector = get_inspector()
    columns = [col['name'] for col in inspector.get_columns(table_name, schema=schema)]
    return column_name in columns


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. PostgreSQL Enum Types
    if is_postgres:
        try:
            op.execute(sa.text("DO $$ BEGIN CREATE TYPE accounttype AS ENUM ('STUDENT', 'MENTOR', 'ADMIN', 'RECRUITER'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
            op.execute(sa.text("DO $$ BEGIN CREATE TYPE accountstatus AS ENUM ('ACTIVE', 'PENDING', 'SUSPENDED', 'REJECTED'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
            op.execute(sa.text("DO $$ BEGIN CREATE TYPE mentorapplicationstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
        except Exception:
            pass

    # 2. Add columns to users table
    if table_exists('users'):
        if not column_exists('users', 'account_type'):
            op.add_column(
                'users',
                sa.Column(
                    'account_type',
                    sa.Enum('STUDENT', 'MENTOR', 'ADMIN', 'RECRUITER', name='accounttype', create_type=False),
                    nullable=False,
                    server_default='STUDENT'
                )
            )
        if not column_exists('users', 'status'):
            op.add_column(
                'users',
                sa.Column(
                    'status',
                    sa.Enum('ACTIVE', 'PENDING', 'SUSPENDED', 'REJECTED', name='accountstatus', create_type=False),
                    nullable=False,
                    server_default='ACTIVE'
                )
            )

        # Backfill existing users: If user is superuser or has ADMIN membership -> ADMIN, if has MENTOR -> MENTOR, else STUDENT
        try:
            op.execute(sa.text("UPDATE users SET account_type = 'ADMIN' WHERE is_superuser = true"))
            if table_exists('organization_memberships'):
                op.execute(sa.text("""
                    UPDATE users SET account_type = 'ADMIN'
                    WHERE id IN (SELECT user_id FROM organization_memberships WHERE role = 'ADMIN')
                """))
                op.execute(sa.text("""
                    UPDATE users SET account_type = 'MENTOR'
                    WHERE id IN (SELECT user_id FROM organization_memberships WHERE role = 'MENTOR')
                    AND account_type != 'ADMIN'
                """))
        except Exception:
            pass

    # 3. Create mentor_applications table
    if not table_exists('mentor_applications'):
        from sqlalchemy.dialects import postgresql as pg_types

        status_enum = (
            pg_types.ENUM('PENDING', 'APPROVED', 'REJECTED', name='mentorapplicationstatus', create_type=False)
            if is_postgres
            else sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='mentorapplicationstatus')
        )

        op.create_table(
            'mentor_applications',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('full_name', sa.String(255), nullable=False),
            sa.Column('official_email', sa.String(255), nullable=False, index=True),
            sa.Column('institute_name', sa.String(255), nullable=False),
            sa.Column('employee_id', sa.String(100), nullable=False),
            sa.Column('department', sa.String(150), nullable=True),
            sa.Column('designation', sa.String(150), nullable=True),
            sa.Column(
                'status',
                status_enum,
                nullable=False,
                server_default='PENDING'
            ),
            sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('rejection_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
        )


def downgrade() -> None:
    if table_exists('mentor_applications'):
        op.drop_table('mentor_applications')
    if table_exists('users'):
        if column_exists('users', 'status'):
            op.drop_column('users', 'status')
        if column_exists('users', 'account_type'):
            op.drop_column('users', 'account_type')
