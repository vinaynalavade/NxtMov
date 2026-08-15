import os
import tempfile
import pytest
from sqlalchemy import create_engine, inspect, text
from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.core.migration_runner import (
    run_database_migrations,
    get_current_alembic_revision,
    has_existing_app_schema,
    INITIAL_REVISION,
    HEAD_REVISION,
)
from app.core.database import engine, SessionLocal
from app.models.user import User


def get_test_alembic_config(db_url: str) -> Config:
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")
    alembic_dir_path = os.path.join(backend_dir, "alembic")
    
    cfg = Config(alembic_ini_path)
    cfg.set_main_option("script_location", alembic_dir_path)
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def run_test_migration_runner(db_url: str):
    """
    Helper to run the migration bootstrap against a specific test database engine.
    """
    cfg = get_test_alembic_config(db_url)
    test_engine = create_engine(db_url)
    try:
        with test_engine.connect() as conn:
            current_rev = get_current_alembic_revision(conn)
            has_schema = has_existing_app_schema(conn)

            if current_rev is None and has_schema:
                command.stamp(cfg, INITIAL_REVISION)

        command.upgrade(cfg, "head")

        with test_engine.connect() as conn:
            final_rev = get_current_alembic_revision(conn)

        if final_rev != HEAD_REVISION:
            raise RuntimeError(f"Migration did not reach head: {final_rev}")
        return final_rev
    finally:
        test_engine.dispose()


def test_migration_scenario_1_empty_database():
    """
    1. Empty database: Starts with no tables.
    Runs migration -> ebc0d3f036ab -> a1b2c3d4e5f6.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = f.name

    try:
        db_url = f"sqlite:///{temp_db_path}"
        test_eng = create_engine(db_url)
        try:
            # Confirm empty
            inspector = inspect(test_eng)
            assert len(inspector.get_table_names()) == 0
        finally:
            test_eng.dispose()

        final_rev = run_test_migration_runner(db_url)
        assert final_rev == HEAD_REVISION

        # Inspect resulting schema
        test_eng = create_engine(db_url)
        try:
            inspector = inspect(test_eng)
            tables = set(inspector.get_table_names())
            assert "users" in tables
            assert "student_profiles" in tables
            assert "resumes" in tables
            assert "resume_analyses" in tables
            assert "candidate_interactions" in tables
            assert "job_recommendations" in tables
            assert "notifications" in tables

            user_cols = [c["name"] for c in inspector.get_columns("users")]
            assert "is_email_verified" in user_cols
            assert "is_phone_verified" in user_cols
            assert "email_verification_token" in user_cols
            assert "phone_otp" in user_cols
            assert "password_reset_token" in user_cols
        finally:
            test_eng.dispose()
    finally:
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except Exception:
                pass


def test_migration_scenario_2_existing_db_without_alembic_version_and_missing_is_email_verified():
    """
    2, 3, 5, 6, 7, 10, L, M, N:
    Simulates Render production database:
    - Existing schema (users, organizations) created without alembic_version.
    - Missing is_email_verified, is_phone_verified, email_verification_token, phone_otp, password_reset_token.
    - Contains real existing user vinaynalavadeooo7@gmail.com with password hash.
    - Verifies baseline stamping, upgrade, user & password hash preservation, and auth login.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = f.name

    try:
        db_url = f"sqlite:///{temp_db_path}"
        test_eng = create_engine(db_url)
        raw_password = "VinayProductionPassword@2026"
        original_hashed_password = get_password_hash(raw_password)

        try:
            # 1. Create the legacy initial table structure WITHOUT is_email_verified
            with test_eng.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE users (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        email VARCHAR(255) NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255) NOT NULL,
                        phone VARCHAR(50),
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        is_superuser BOOLEAN NOT NULL DEFAULT 0,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.execute(text("""
                    CREATE TABLE organizations (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) NOT NULL,
                        slug VARCHAR(255) NOT NULL,
                        type VARCHAR(50) NOT NULL DEFAULT 'INDIVIDUAL',
                        owner_id INTEGER NOT NULL,
                        phone VARCHAR(50),
                        website VARCHAR(255),
                        location VARCHAR(255),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """))

                conn.execute(text("""
                    INSERT INTO users (email, hashed_password, full_name, phone, is_active, is_superuser)
                    VALUES (:email, :pwd, :name, :phone, 1, 1)
                """), {
                    "email": "vinaynalavadeooo7@gmail.com",
                    "pwd": original_hashed_password,
                    "name": "Vinay Nalavade",
                    "phone": "+919876543210"
                })

            # Confirm pre-migration state: no alembic_version, users table exists
            with test_eng.connect() as conn:
                assert get_current_alembic_revision(conn) is None
                assert has_existing_app_schema(conn) is True

                # Verify query fails if asking for is_email_verified
                with pytest.raises(Exception):
                    conn.execute(text("SELECT is_email_verified FROM users WHERE email = 'vinaynalavadeooo7@gmail.com'"))

                # Query email before migration
                res = conn.execute(text("SELECT email, hashed_password FROM users WHERE email = 'vinaynalavadeooo7@gmail.com'")).fetchone()
                assert res is not None
                assert res[0] == "vinaynalavadeooo7@gmail.com"
                assert res[1] == original_hashed_password
        finally:
            test_eng.dispose()

        # 2. Run the production migration runner
        final_rev = run_test_migration_runner(db_url)
        assert final_rev == HEAD_REVISION

        # 3. Verify post-migration state
        test_eng = create_engine(db_url)
        try:
            with test_eng.connect() as conn:
                # Check revision
                assert get_current_alembic_revision(conn) == HEAD_REVISION

                # L. Specifically verify: SELECT email FROM users WHERE email = 'vinaynalavadeooo7@gmail.com'
                email_row = conn.execute(text("SELECT email FROM users WHERE email = 'vinaynalavadeooo7@gmail.com'")).fetchone()
                assert email_row is not None
                assert email_row[0] == "vinaynalavadeooo7@gmail.com"

                # Check hashed_password is unchanged before/after migration
                user_row = conn.execute(text("""
                    SELECT
                        id,
                        email,
                        hashed_password,
                        is_email_verified,
                        is_phone_verified
                    FROM users
                    WHERE email = 'vinaynalavadeooo7@gmail.com'
                """)).fetchone()

                assert user_row is not None
                assert user_row[1] == "vinaynalavadeooo7@gmail.com"
                assert user_row[2] == original_hashed_password, "Password hash must remain byte-for-byte identical!"
                # is_email_verified column exists and has safe boolean default
                assert user_row[3] in (False, 0)
                assert user_row[4] in (False, 0)

                # N. Verify login against the existing account using existing password
                assert verify_password(raw_password, user_row[2]) is True

                # Verify all newly required tables exist
                inspector = inspect(test_eng)
                tables = set(inspector.get_table_names())
                assert "student_profiles" in tables
                assert "resumes" in tables
                assert "resume_analyses" in tables
                assert "candidate_interactions" in tables
                assert "job_recommendations" in tables
                assert "notifications" in tables
        finally:
            test_eng.dispose()
    finally:
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except Exception:
                pass


def test_migration_scenario_4_existing_db_with_initial_revision_stamped():
    """
    4. Existing database with ebc0d3f036ab:
    Starts with alembic_version = ebc0d3f036ab. Upgrades to a1b2c3d4e5f6.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = f.name

    try:
        db_url = f"sqlite:///{temp_db_path}"
        cfg = get_test_alembic_config(db_url)

        # Upgrade to ebc0d3f036ab first
        command.upgrade(cfg, INITIAL_REVISION)

        test_eng = create_engine(db_url)
        try:
            with test_eng.connect() as conn:
                assert get_current_alembic_revision(conn) == INITIAL_REVISION
        finally:
            test_eng.dispose()

        # Run migration runner
        final_rev = run_test_migration_runner(db_url)
        assert final_rev == HEAD_REVISION

        test_eng = create_engine(db_url)
        try:
            with test_eng.connect() as conn:
                assert get_current_alembic_revision(conn) == HEAD_REVISION
        finally:
            test_eng.dispose()
    finally:
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except Exception:
                pass


def test_migration_scenario_8_migration_idempotency():
    """
    8. Migration idempotency:
    Running the migration runner multiple times must be safe, stable, and leave revision at a1b2c3d4e5f6.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = f.name

    try:
        db_url = f"sqlite:///{temp_db_path}"

        # Run 1
        rev1 = run_test_migration_runner(db_url)
        assert rev1 == HEAD_REVISION

        # Run 2
        rev2 = run_test_migration_runner(db_url)
        assert rev2 == HEAD_REVISION

        # Run 3
        rev3 = run_test_migration_runner(db_url)
        assert rev3 == HEAD_REVISION
    finally:
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except Exception:
                pass


def test_app_configured_database_schema_and_startup_runner():
    """
    Verifies that the application's actual configured database has all required columns and tables
    and that run_database_migrations() executes with success.
    """
    # Execute actual application startup runner
    run_database_migrations()

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
        assert col in user_columns, f"Column {col} missing from users table schema!"

    db = SessionLocal()
    try:
        # Full query with all verification columns
        user = db.query(User).filter(User.email == "demo@nxtmov.local").first()
        if user:
            assert hasattr(user, "is_email_verified")
            assert hasattr(user, "is_phone_verified")
            assert hasattr(user, "email_verification_token")
            assert hasattr(user, "phone_otp")
            assert hasattr(user, "password_reset_token")
    finally:
        db.close()
