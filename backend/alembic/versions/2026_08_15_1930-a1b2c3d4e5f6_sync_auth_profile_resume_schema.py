"""sync_auth_profile_resume_schema

Revision ID: a1b2c3d4e5f6
Revises: ebc0d3f036ab
Create Date: 2026-08-15 19:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ebc0d3f036ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_inspector():
    bind = op.get_bind()
    return sa.inspect(bind)


def column_exists(table_name: str, column_name: str, schema: str = None) -> bool:
    inspector = get_inspector()
    if not table_exists(table_name, schema=schema):
        return False
    columns = [c["name"] for c in inspector.get_columns(table_name, schema=schema)]
    return column_name in columns


def table_exists(table_name: str, schema: str = None) -> bool:
    inspector = get_inspector()
    return table_name in inspector.get_table_names(schema=schema)


def index_exists(table_name: str, index_name: str, schema: str = None) -> bool:
    inspector = get_inspector()
    if not table_exists(table_name, schema=schema):
        return False
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name, schema=schema)]
    return index_name in indexes


def upgrade() -> None:
    # =========================================================================
    # 1. USERS TABLE - Add email verification, phone OTP & reset token fields
    # =========================================================================
    if table_exists('users'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            if not column_exists('users', 'is_email_verified'):
                batch_op.add_column(
                    sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false'))
                )
            if not column_exists('users', 'is_phone_verified'):
                batch_op.add_column(
                    sa.Column('is_phone_verified', sa.Boolean(), nullable=False, server_default=sa.text('false'))
                )
            if not column_exists('users', 'email_verification_token'):
                batch_op.add_column(
                    sa.Column('email_verification_token', sa.String(length=255), nullable=True)
                )
            if not column_exists('users', 'phone_otp'):
                batch_op.add_column(
                    sa.Column('phone_otp', sa.String(length=20), nullable=True)
                )
            if not column_exists('users', 'password_reset_token'):
                batch_op.add_column(
                    sa.Column('password_reset_token', sa.String(length=255), nullable=True)
                )

    # =========================================================================
    # 2. STUDENT PROFILES TABLE
    # =========================================================================
    if not table_exists('student_profiles'):
        op.create_table(
            'student_profiles',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('candidate_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('avatar_url', sa.String(length=500), nullable=True),
            sa.Column('city', sa.String(length=100), nullable=True),
            sa.Column('state', sa.String(length=100), nullable=True),
            sa.Column('country', sa.String(length=100), nullable=True, server_default='India'),
            sa.Column('headline', sa.String(length=255), nullable=True),
            sa.Column('career_objective', sa.Text(), nullable=True),
            sa.Column('preferred_roles', sa.Text(), nullable=True),
            sa.Column('preferred_locations', sa.Text(), nullable=True),
            sa.Column('employment_preference', sa.String(length=50), nullable=True, server_default='FULL_TIME'),
            sa.Column('expected_salary', sa.Float(), nullable=True),
            sa.Column('notice_period_days', sa.Integer(), nullable=True),
            sa.Column('highest_qualification', sa.String(length=150), nullable=True),
            sa.Column('degree', sa.String(length=150), nullable=True),
            sa.Column('college_university', sa.String(length=255), nullable=True),
            sa.Column('graduation_year', sa.Integer(), nullable=True),
            sa.Column('specialization', sa.String(length=150), nullable=True),
            sa.Column('cgpa_or_percentage', sa.String(length=50), nullable=True),
            sa.Column('programming_languages', sa.Text(), nullable=True),
            sa.Column('frameworks', sa.Text(), nullable=True),
            sa.Column('testing_tools', sa.Text(), nullable=True),
            sa.Column('databases', sa.Text(), nullable=True),
            sa.Column('cloud_technologies', sa.Text(), nullable=True),
            sa.Column('soft_skills', sa.Text(), nullable=True),
            sa.Column('experience_json', sa.Text(), nullable=True),
            sa.Column('projects_json', sa.Text(), nullable=True),
            sa.Column('certifications_json', sa.Text(), nullable=True),
            sa.Column('linkedin_url', sa.String(length=500), nullable=True),
            sa.Column('github_url', sa.String(length=500), nullable=True),
            sa.Column('portfolio_url', sa.String(length=500), nullable=True),
            sa.Column('other_links_json', sa.Text(), nullable=True),
            sa.Column('email_notifications_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('job_alerts_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('completeness_score', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], name=op.f('fk_student_profiles_candidate_id_candidates'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_student_profiles_organization_id_organizations'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_student_profiles_user_id_users'), ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_student_profiles')),
            sa.UniqueConstraint('candidate_id', name=op.f('uq_student_profiles_candidate_id'))
        )
        with op.batch_alter_table('student_profiles', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_student_profiles_candidate_id'), ['candidate_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_student_profiles_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_student_profiles_organization_id'), ['organization_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_student_profiles_user_id'), ['user_id'], unique=False)
            batch_op.create_index('ix_student_profiles_cand_user', ['candidate_id', 'user_id'], unique=False)

    # =========================================================================
    # 3. RESUMES TABLE
    # =========================================================================
    if not table_exists('resumes'):
        op.create_table(
            'resumes',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('candidate_id', sa.Integer(), nullable=False),
            sa.Column('file_name', sa.String(length=255), nullable=False),
            sa.Column('file_type', sa.String(length=100), nullable=False),
            sa.Column('file_url', sa.String(length=500), nullable=False),
            sa.Column('file_size_bytes', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('extracted_text', sa.Text(), nullable=True),
            sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('quality_score', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('career_domain', sa.String(length=100), nullable=True),
            sa.Column('likely_roles_json', sa.Text(), nullable=True),
            sa.Column('domain_explanation', sa.Text(), nullable=True),
            sa.Column('strengths_json', sa.Text(), nullable=True),
            sa.Column('improvements_json', sa.Text(), nullable=True),
            sa.Column('warnings_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], name=op.f('fk_resumes_candidate_id_candidates'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_resumes_organization_id_organizations'), ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_resumes'))
        )
        with op.batch_alter_table('resumes', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_resumes_candidate_id'), ['candidate_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_resumes_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_resumes_organization_id'), ['organization_id'], unique=False)

    # =========================================================================
    # 4. RESUME ANALYSES TABLE
    # =========================================================================
    if not table_exists('resume_analyses'):
        op.create_table(
            'resume_analyses',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('resume_id', sa.Integer(), nullable=False),
            sa.Column('candidate_id', sa.Integer(), nullable=False),
            sa.Column('parsed_data_json', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING_REVIEW'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], name=op.f('fk_resume_analyses_candidate_id_candidates'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_resume_analyses_organization_id_organizations'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], name=op.f('fk_resume_analyses_resume_id_resumes'), ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_resume_analyses'))
        )
        with op.batch_alter_table('resume_analyses', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_resume_analyses_candidate_id'), ['candidate_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_resume_analyses_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_resume_analyses_organization_id'), ['organization_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_resume_analyses_resume_id'), ['resume_id'], unique=False)

    # =========================================================================
    # 5. CANDIDATE INTERACTIONS TABLE
    # =========================================================================
    if not table_exists('candidate_interactions'):
        op.create_table(
            'candidate_interactions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('candidate_id', sa.Integer(), nullable=False),
            sa.Column('created_by_user_id', sa.Integer(), nullable=False),
            sa.Column('contact_id', sa.Integer(), nullable=True),
            sa.Column('company_name', sa.String(length=255), nullable=True),
            sa.Column('hr_name', sa.String(length=255), nullable=True),
            sa.Column('interaction_type', sa.String(length=50), nullable=False, server_default='CALL'),
            sa.Column('outcome', sa.String(length=100), nullable=False, server_default='CONNECTED'),
            sa.Column('notes', sa.Text(), nullable=False),
            sa.Column('next_move', sa.String(length=255), nullable=True),
            sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('interaction_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], name=op.f('fk_candidate_interactions_candidate_id_candidates'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], name=op.f('fk_candidate_interactions_contact_id_contacts'), ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_candidate_interactions_created_by_user_id_users'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_candidate_interactions_organization_id_organizations'), ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_candidate_interactions'))
        )
        with op.batch_alter_table('candidate_interactions', schema=None) as batch_op:
            batch_op.create_index('ix_candidate_interactions_cand', ['candidate_id', 'created_at'], unique=False)
            batch_op.create_index(batch_op.f('ix_candidate_interactions_candidate_id'), ['candidate_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_candidate_interactions_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_candidate_interactions_organization_id'), ['organization_id'], unique=False)

    # =========================================================================
    # 6. JOB RECOMMENDATIONS TABLE
    # =========================================================================
    if not table_exists('job_recommendations'):
        op.create_table(
            'job_recommendations',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('candidate_id', sa.Integer(), nullable=False),
            sa.Column('job_requirement_id', sa.Integer(), nullable=False),
            sa.Column('match_score', sa.Float(), nullable=False, server_default=sa.text('0.0')),
            sa.Column('score_breakdown_json', sa.Text(), nullable=True),
            sa.Column('is_saved', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('is_dismissed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], name=op.f('fk_job_recommendations_candidate_id_candidates'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['job_requirement_id'], ['job_requirements.id'], name=op.f('fk_job_recommendations_job_requirement_id_job_requirements'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_job_recommendations_organization_id_organizations'), ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_job_recommendations'))
        )
        with op.batch_alter_table('job_recommendations', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_job_recommendations_candidate_id'), ['candidate_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_job_recommendations_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_job_recommendations_job_requirement_id'), ['job_requirement_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_job_recommendations_organization_id'), ['organization_id'], unique=False)
            batch_op.create_index('ix_job_rec_cand_req', ['candidate_id', 'job_requirement_id'], unique=True)

    # =========================================================================
    # 7. NOTIFICATIONS TABLE
    # =========================================================================
    if not table_exists('notifications'):
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('notification_type', sa.String(length=50), nullable=False, server_default='INFO'),
            sa.Column('link_url', sa.String(length=500), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_notifications_organization_id_organizations'), ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_notifications_user_id_users'), ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_notifications'))
        )
        with op.batch_alter_table('notifications', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_notifications_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_notifications_organization_id'), ['organization_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_notifications_user_id'), ['user_id'], unique=False)
            batch_op.create_index('ix_notifications_user_read', ['user_id', 'is_read'], unique=False)


def downgrade() -> None:
    if table_exists('notifications'):
        with op.batch_alter_table('notifications', schema=None) as batch_op:
            batch_op.drop_index('ix_notifications_user_read')
            batch_op.drop_index(batch_op.f('ix_notifications_user_id'))
            batch_op.drop_index(batch_op.f('ix_notifications_organization_id'))
            batch_op.drop_index(batch_op.f('ix_notifications_id'))
        op.drop_table('notifications')

    if table_exists('job_recommendations'):
        with op.batch_alter_table('job_recommendations', schema=None) as batch_op:
            batch_op.drop_index('ix_job_rec_cand_req')
            batch_op.drop_index(batch_op.f('ix_job_recommendations_organization_id'))
            batch_op.drop_index(batch_op.f('ix_job_recommendations_job_requirement_id'))
            batch_op.drop_index(batch_op.f('ix_job_recommendations_id'))
            batch_op.drop_index(batch_op.f('ix_job_recommendations_candidate_id'))
        op.drop_table('job_recommendations')

    if table_exists('candidate_interactions'):
        with op.batch_alter_table('candidate_interactions', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_candidate_interactions_organization_id'))
            batch_op.drop_index(batch_op.f('ix_candidate_interactions_id'))
            batch_op.drop_index(batch_op.f('ix_candidate_interactions_candidate_id'))
            batch_op.drop_index('ix_candidate_interactions_cand')
        op.drop_table('candidate_interactions')

    if table_exists('resume_analyses'):
        with op.batch_alter_table('resume_analyses', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_resume_analyses_resume_id'))
            batch_op.drop_index(batch_op.f('ix_resume_analyses_organization_id'))
            batch_op.drop_index(batch_op.f('ix_resume_analyses_id'))
            batch_op.drop_index(batch_op.f('ix_resume_analyses_candidate_id'))
        op.drop_table('resume_analyses')

    if table_exists('resumes'):
        with op.batch_alter_table('resumes', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_resumes_organization_id'))
            batch_op.drop_index(batch_op.f('ix_resumes_id'))
            batch_op.drop_index(batch_op.f('ix_resumes_candidate_id'))
        op.drop_table('resumes')

    if table_exists('student_profiles'):
        with op.batch_alter_table('student_profiles', schema=None) as batch_op:
            batch_op.drop_index('ix_student_profiles_cand_user')
            batch_op.drop_index(batch_op.f('ix_student_profiles_user_id'))
            batch_op.drop_index(batch_op.f('ix_student_profiles_organization_id'))
            batch_op.drop_index(batch_op.f('ix_student_profiles_id'))
            batch_op.drop_index(batch_op.f('ix_student_profiles_candidate_id'))
        op.drop_table('student_profiles')

    if table_exists('users'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            if column_exists('users', 'password_reset_token'):
                batch_op.drop_column('password_reset_token')
            if column_exists('users', 'phone_otp'):
                batch_op.drop_column('phone_otp')
            if column_exists('users', 'email_verification_token'):
                batch_op.drop_column('email_verification_token')
            if column_exists('users', 'is_phone_verified'):
                batch_op.drop_column('is_phone_verified')
            if column_exists('users', 'is_email_verified'):
                batch_op.drop_column('is_email_verified')
