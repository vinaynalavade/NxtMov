import pytest
from sqlalchemy import inspect, text
from app.core.database import engine, SessionLocal
from app.models.user import User
from app.main import apply_database_migrations

def test_database_schema_contains_all_user_verification_and_auth_columns():
    inspector = inspect(engine)
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    
    required_columns = [
        "id",
        "email",
        "hashed_password",
        "full_name",
        "phone",
        "is_active",
        "is_superuser",
        "is_email_verified",
        "is_phone_verified",
        "email_verification_token",
        "phone_otp",
        "password_reset_token",
        "created_at",
        "updated_at"
    ]
    
    for col in required_columns:
        assert col in user_columns, f"Column {col} is missing from the users table schema!"

def test_database_schema_contains_all_application_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = [
        "users",
        "organizations",
        "organization_memberships",
        "candidates",
        "student_profiles",
        "resumes",
        "resume_analyses",
        "candidate_interactions",
        "job_recommendations",
        "notifications",
        "companies",
        "contacts",
        "job_requirements",
        "applications",
        "submissions",
        "interviews",
        "offers",
        "placements",
        "calls",
        "followups",
        "audit_logs"
    ]
    
    for tbl in required_tables:
        assert tbl in tables, f"Table {tbl} is missing from the database schema!"

def test_user_query_selects_all_auth_fields_without_sql_error():
    db = SessionLocal()
    try:
        # Execute the exact production query structure that failed
        user = db.query(User).filter(User.email == "demo@nxtmov.local").first()
        if user:
            assert hasattr(user, "is_email_verified")
            assert hasattr(user, "is_phone_verified")
            assert hasattr(user, "email_verification_token")
            assert hasattr(user, "phone_otp")
            assert hasattr(user, "password_reset_token")
    finally:
        db.close()

def test_migration_runner_is_idempotent():
    # Calling apply_database_migrations() multiple times must be safe and harmless
    apply_database_migrations()
    apply_database_migrations()
