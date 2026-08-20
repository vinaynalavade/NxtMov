import os
import json
import tempfile
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
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
from app.models.organization import Organization, OrganizationMembership, OrgType, OrgRole
from app.models.candidate import Candidate, CandidateStatus, Document, DocumentType
from app.models.student_profile import StudentProfile
from app.models.resume import Resume, ResumeAnalysis
from app.services.resume_service import (
    extract_text_from_file_bytes,
    parse_resume_text,
    calculate_ats_score,
)


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
            raise RuntimeError(f"Migration did not reach head {HEAD_REVISION}: got {final_rev}")
        return final_rev
    finally:
        test_engine.dispose()


def test_migration_scenario_1_empty_database():
    """
    1. Empty database: Starts with no tables.
    Runs migration -> ebc0d3f036ab -> a1b2c3d4e5f6 -> f1e2d3c4b5a6.
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

            resume_cols = [c["name"] for c in inspector.get_columns("resumes")]
            assert "career_domain" in resume_cols
            assert "quality_score" in resume_cols
            assert "likely_roles_json" in resume_cols
            assert "domain_explanation" in resume_cols
            assert "strengths_json" in resume_cols
            assert "improvements_json" in resume_cols
            assert "warnings_json" in resume_cols
            assert "extracted_text" in resume_cols
            assert "is_current" in resume_cols
            assert "file_size_bytes" in resume_cols
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

            # Confirm pre-migration state
            with test_eng.connect() as conn:
                assert get_current_alembic_revision(conn) is None
                assert has_existing_app_schema(conn) is True

                with pytest.raises(Exception):
                    conn.execute(text("SELECT is_email_verified FROM users WHERE email = 'vinaynalavadeooo7@gmail.com'"))

                res = conn.execute(text("SELECT email, hashed_password FROM users WHERE email = 'vinaynalavadeooo7@gmail.com'")).fetchone()
                assert res is not None
                assert res[0] == "vinaynalavadeooo7@gmail.com"
                assert res[1] == original_hashed_password
        finally:
            test_eng.dispose()

        # Run the production migration runner
        final_rev = run_test_migration_runner(db_url)
        assert final_rev == HEAD_REVISION

        # Verify post-migration state
        test_eng = create_engine(db_url)
        try:
            with test_eng.connect() as conn:
                assert get_current_alembic_revision(conn) == HEAD_REVISION

                email_row = conn.execute(text("SELECT email FROM users WHERE email = 'vinaynalavadeooo7@gmail.com'")).fetchone()
                assert email_row is not None
                assert email_row[0] == "vinaynalavadeooo7@gmail.com"

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
                assert user_row[3] in (False, 0)
                assert user_row[4] in (False, 0)

                assert verify_password(raw_password, user_row[2]) is True

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
    Starts with alembic_version = ebc0d3f036ab. Upgrades to f1e2d3c4b5a6.
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

        # Run migration runner to HEAD
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
    Running the migration runner multiple times must be safe, stable, and leave revision at f1e2d3c4b5a6.
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


def test_migration_scenario_legacy_resumes_missing_analysis_columns():
    """
    Simulates a database with a legacy resumes table missing:
    - career_domain
    - quality_score
    - likely_roles_json
    - domain_explanation
    - strengths_json
    - improvements_json
    - warnings_json

    Verifies that:
    1. Migration safely adds all missing columns without dropping table or losing rows.
    2. Existing resume rows survive with their original data intact.
    3. Existing user and candidate rows remain intact.
    4. SQLAlchemy ORM Resume model can query existing and insert new records.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = f.name

    try:
        db_url = f"sqlite:///{temp_db_path}"
        test_eng = create_engine(db_url)

        try:
            with test_eng.begin() as conn:
                # Create base tables
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
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.execute(text("""
                    CREATE TABLE candidates (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        organization_id INTEGER NOT NULL,
                        user_id INTEGER,
                        full_name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'NEW',
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                # Legacy resumes table missing quality_score, career_domain, etc.
                conn.execute(text("""
                    CREATE TABLE resumes (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        organization_id INTEGER NOT NULL,
                        candidate_id INTEGER NOT NULL,
                        file_name VARCHAR(255) NOT NULL,
                        file_type VARCHAR(100) NOT NULL,
                        file_url VARCHAR(500) NOT NULL,
                        file_size_bytes INTEGER NOT NULL DEFAULT 0,
                        extracted_text TEXT,
                        is_current BOOLEAN NOT NULL DEFAULT 1,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """))

                # Seed rows
                conn.execute(text("""
                    INSERT INTO users (id, email, hashed_password, full_name, phone)
                    VALUES (1, 'vinay@nxtmov.local', 'hashed_pass_123', 'Vinay Nalavade', '+919876543210');
                """))
                conn.execute(text("""
                    INSERT INTO organizations (id, name, slug, owner_id)
                    VALUES (1, 'NxtMov Org', 'nxtmov-org', 1);
                """))
                conn.execute(text("""
                    INSERT INTO candidates (id, organization_id, user_id, full_name, email)
                    VALUES (1, 1, 1, 'Vinay Nalavade', 'vinay@nxtmov.local');
                """))
                conn.execute(text("""
                    INSERT INTO resumes (id, organization_id, candidate_id, file_name, file_type, file_url, file_size_bytes, extracted_text, is_current)
                    VALUES (101, 1, 1, 'legacy_resume.pdf', 'application/pdf', '/api/v1/resumes/101/file', 12345, 'Legacy resume extracted text', 1);
                """))

            # Verify career_domain does NOT exist prior to migration
            with test_eng.connect() as conn:
                with pytest.raises(Exception):
                    conn.execute(text("SELECT career_domain FROM resumes WHERE id = 101"))
        finally:
            test_eng.dispose()

        # Run migration runner
        final_rev = run_test_migration_runner(db_url)
        assert final_rev == HEAD_REVISION

        # Verify columns added and data preserved
        test_eng = create_engine(db_url)
        try:
            with test_eng.connect() as conn:
                row = conn.execute(text("""
                    SELECT id, file_name, quality_score, career_domain, likely_roles_json, strengths_json
                    FROM resumes
                    WHERE id = 101
                """)).fetchone()

                assert row is not None
                assert row[0] == 101
                assert row[1] == "legacy_resume.pdf"
                assert row[2] == 0  # default value for quality_score
                assert row[3] is None  # nullable career_domain
                assert row[4] is None
                assert row[5] is None

            # ORM query test
            TestSession = sessionmaker(bind=test_eng)
            session = TestSession()
            try:
                legacy_resume = session.query(Resume).filter(Resume.id == 101).first()
                assert legacy_resume is not None
                assert legacy_resume.file_name == "legacy_resume.pdf"
                assert legacy_resume.quality_score == 0
                assert legacy_resume.career_domain is None

                # Test inserting a new resume using the ORM model
                new_resume = Resume(
                    organization_id=1,
                    candidate_id=1,
                    file_name="new_test_resume.docx",
                    file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    file_url="/api/v1/resumes/102/file",
                    file_size_bytes=54321,
                    extracted_text="Python FastAPI Full Stack QA Automation",
                    is_current=True,
                    quality_score=92,
                    career_domain="Full Stack Engineering",
                    likely_roles_json=json.dumps(["Full Stack Engineer", "Backend Developer"]),
                    domain_explanation="High match for Python/FastAPI",
                    strengths_json=json.dumps(["Strong backend proficiency"]),
                    improvements_json=json.dumps(["Add cloud certifications"]),
                    warnings_json=json.dumps([])
                )
                session.add(new_resume)
                session.commit()

                queried_new = session.query(Resume).filter(Resume.id == new_resume.id).first()
                assert queried_new is not None
                assert queried_new.career_domain == "Full Stack Engineering"
                assert queried_new.quality_score == 92
                assert "Full Stack Engineer" in queried_new.likely_roles_json
            finally:
                session.close()
        finally:
            test_eng.dispose()
    finally:
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except Exception:
                pass


def test_exact_production_scenario_and_resume_upload_orm_flow():
    """
    Simulates the exact Render production error situation:
    - Existing users table with Vinay Nalavade account (vinaynalavadeooo7@gmail.com)
    - Existing organizations table
    - Existing organization_memberships table
    - Existing candidates table
    - Existing student_profiles table
    - Existing resumes table missing career_domain and all analysis columns
    - An existing legacy resume row

    Then:
    1. Executes migration bootstrap -> verifies HEAD revision f1e2d3c4b5a6 reached.
    2. Runs the exact ORM pipeline used in POST /api/v1/resumes/upload.
    3. Verifies quality_score=89, career_domain='Quality Assurance & Test Automation',
       likely_roles_json, domain_explanation, strengths_json, improvements_json, warnings_json
       are persisted without any UndefinedColumn or PostgreSQL-equivalent errors.
    4. Verifies Vinay Nalavade's account, password hash, and relations remain 100% intact.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db_path = f.name

    try:
        db_url = f"sqlite:///{temp_db_path}"
        test_eng = create_engine(db_url)
        vinay_raw_password = "VinayProductionSecret@2026"
        vinay_password_hash = get_password_hash(vinay_raw_password)

        try:
            with test_eng.begin() as conn:
                # 1. Users table (pre-migration state)
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
                # 2. Organizations table
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
                # 3. Candidates table
                conn.execute(text("""
                    CREATE TABLE candidates (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        organization_id INTEGER NOT NULL,
                        user_id INTEGER,
                        full_name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        phone VARCHAR(50),
                        location VARCHAR(255),
                        current_title VARCHAR(150),
                        current_company VARCHAR(150),
                        experience_years FLOAT,
                        notice_period_days INTEGER,
                        current_salary NUMERIC(12,2),
                        expected_salary NUMERIC(12,2),
                        primary_skills TEXT,
                        secondary_skills TEXT,
                        skills TEXT,
                        assigned_counselor_id INTEGER,
                        assigned_recruiter_id INTEGER,
                        source VARCHAR(100),
                        resume_url VARCHAR(500),
                        status VARCHAR(50) NOT NULL DEFAULT 'NEW',
                        notes TEXT,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                # 4. Documents table
                conn.execute(text("""
                    CREATE TABLE documents (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        organization_id INTEGER NOT NULL,
                        candidate_id INTEGER NOT NULL,
                        file_name VARCHAR(255) NOT NULL,
                        file_type VARCHAR(100) NOT NULL,
                        file_url VARCHAR(500) NOT NULL,
                        doc_type VARCHAR(50) NOT NULL DEFAULT 'RESUME',
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                # 5. Legacy Resumes table (exact production issue: MISSING career_domain, quality_score, etc.)
                conn.execute(text("""
                    CREATE TABLE resumes (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        organization_id INTEGER NOT NULL,
                        candidate_id INTEGER NOT NULL,
                        file_name VARCHAR(255) NOT NULL,
                        file_type VARCHAR(100) NOT NULL,
                        file_url VARCHAR(500) NOT NULL,
                        file_size_bytes INTEGER NOT NULL DEFAULT 0,
                        extracted_text TEXT,
                        is_current BOOLEAN NOT NULL DEFAULT 1,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """))

                # Seed Vinay's account and existing legacy data
                conn.execute(text("""
                    INSERT INTO users (id, email, hashed_password, full_name, phone, is_active, is_superuser)
                    VALUES (1, 'vinaynalavadeooo7@gmail.com', :pwd, 'Vinay Nalavade', '+919876543210', 1, 1);
                """), {"pwd": vinay_password_hash})

                conn.execute(text("""
                    INSERT INTO organizations (id, name, slug, type, owner_id)
                    VALUES (1, 'NxtMov Production Org', 'nxtmov-prod', 'INDIVIDUAL', 1);
                """))

                conn.execute(text("""
                    INSERT INTO candidates (id, organization_id, user_id, full_name, email, phone, status)
                    VALUES (1, 1, 1, 'Vinay Nalavade', 'vinaynalavadeooo7@gmail.com', '+919876543210', 'READY');
                """))

                conn.execute(text("""
                    INSERT INTO resumes (id, organization_id, candidate_id, file_name, file_type, file_url, file_size_bytes, extracted_text, is_current)
                    VALUES (10, 1, 1, 'Vinay_Original_Old_Resume.pdf', 'application/pdf', '/api/v1/resumes/10/file', 20480, 'Original legacy resume text', 1);
                """))

            # Pre-migration verification: confirm missing column causes error if queried
            with test_eng.connect() as conn:
                with pytest.raises(Exception):
                    conn.execute(text("SELECT career_domain FROM resumes"))
        finally:
            test_eng.dispose()

        # Step 1: Run migration runner
        final_rev = run_test_migration_runner(db_url)
        assert final_rev == HEAD_REVISION

        # Step 2: Execute exact ORM operations from POST /api/v1/resumes/upload
        test_eng = create_engine(db_url)
        TestSession = sessionmaker(bind=test_eng)
        session = TestSession()

        try:
            # Simulate parsed QA Automation text with 4879 characters (as in production log)
            simulated_qa_text = (
                "Neha Patel - Senior QA & Test Automation Specialist\n"
                "Summary: 6 years of expertise in Test Automation, Selenium WebDriver, Playwright, Pytest, Postman, "
                "API Testing, CI/CD Jenkins pipelines, Defect Management, Performance Testing with JMeter.\n"
                "Experience: Automated 1200+ end-to-end regression test cases across web and microservice platforms. "
                "Architected robust automation framework with 98% pass rate and integrated with GitHub Actions.\n"
                "Skills: Python, Java, Selenium, Playwright, TestNG, Pytest, Postman, RestAssured, Git, Docker, AWS.\n"
                + ("Detailed test planning, quality assurance execution, traceability matrix, automated reporting.\n" * 45)
            )
            assert len(simulated_qa_text) >= 3000

            parsed = parse_resume_text(simulated_qa_text)
            ats_result = calculate_ats_score(simulated_qa_text, parsed)
            ats_result["ats_score"] = 89
            ats_result["career_domain"] = "Quality Assurance & Test Automation"

            candidate = session.query(Candidate).filter(Candidate.id == 1).first()
            assert candidate is not None

            # Mark existing resumes not current
            session.query(Resume).filter(
                Resume.organization_id == 1,
                Resume.candidate_id == candidate.id
            ).update({"is_current": False})

            # Create new Resume record with all intelligence fields
            new_resume = Resume(
                organization_id=1,
                candidate_id=candidate.id,
                file_name="Neha_Patel_QA_Automation.pdf",
                file_type="application/pdf",
                file_url="/api/v1/resumes/resume_1_qa_upload.pdf",
                file_size_bytes=len(simulated_qa_text.encode("utf-8")),
                extracted_text=simulated_qa_text,
                is_current=True,
                quality_score=ats_result["ats_score"],
                career_domain=ats_result.get("career_domain") or "General Technical Profile",
                likely_roles_json=json.dumps(ats_result.get("likely_roles", ["QA Engineer", "SDET"])),
                domain_explanation=ats_result.get("domain_explanation") or "Quality Assurance matched profile",
                strengths_json=json.dumps(ats_result.get("strengths", ["✓ Test automation framework development"])),
                improvements_json=json.dumps(ats_result.get("improvements", ["• Add cloud certification details"])),
                warnings_json=json.dumps(ats_result.get("warnings", []))
            )
            session.add(new_resume)
            session.flush()

            # Sync Candidate document
            candidate.resume_url = f"/api/v1/resumes/{new_resume.id}/file"
            doc = Document(
                organization_id=1,
                candidate_id=candidate.id,
                file_name="Neha_Patel_QA_Automation.pdf",
                file_type="application/pdf",
                file_url=f"/api/v1/resumes/{new_resume.id}/file",
                doc_type=DocumentType.RESUME
            )
            session.add(doc)

            # Create ResumeAnalysis record
            analysis = ResumeAnalysis(
                organization_id=1,
                resume_id=new_resume.id,
                candidate_id=candidate.id,
                parsed_data_json=json.dumps(parsed),
                status="PENDING_REVIEW"
            )
            session.add(analysis)
            session.commit()

            # Step 3: Assertions on persisted entities
            # Check new resume
            persisted_resume = session.query(Resume).filter(Resume.id == new_resume.id).first()
            assert persisted_resume is not None
            assert persisted_resume.career_domain == "Quality Assurance & Test Automation"
            assert persisted_resume.quality_score == 89
            assert persisted_resume.is_current is True
            assert "QA" in persisted_resume.likely_roles_json or "SDET" in persisted_resume.likely_roles_json
            assert len(persisted_resume.strengths_json) > 5
            assert len(persisted_resume.improvements_json) > 5

            # Check legacy resume
            legacy_resume = session.query(Resume).filter(Resume.id == 10).first()
            assert legacy_resume is not None
            assert legacy_resume.file_name == "Vinay_Original_Old_Resume.pdf"
            assert legacy_resume.is_current is False
            assert legacy_resume.quality_score == 0
            assert legacy_resume.career_domain is None

            # Check ResumeAnalysis record
            persisted_analysis = session.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == new_resume.id).first()
            assert persisted_analysis is not None
            assert persisted_analysis.status == "PENDING_REVIEW"

            # Check Candidate document and resume_url
            assert candidate.resume_url == f"/api/v1/resumes/{new_resume.id}/file"

            # Step 4: Verify Vinay's account, password hash, and auth verification
            vinay_user = session.query(User).filter(User.email == "vinaynalavadeooo7@gmail.com").first()
            assert vinay_user is not None
            assert vinay_user.full_name == "Vinay Nalavade"
            assert vinay_user.hashed_password == vinay_password_hash
            assert verify_password(vinay_raw_password, vinay_user.hashed_password) is True
        finally:
            session.close()
            test_eng.dispose()
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

    required_user_columns = [
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

    for col in required_user_columns:
        assert col in user_columns, f"Column {col} missing from users table schema!"

    resume_columns = [col["name"] for col in inspector.get_columns("resumes")]
    required_resume_columns = [
        "id",
        "organization_id",
        "candidate_id",
        "file_name",
        "file_type",
        "file_url",
        "file_size_bytes",
        "extracted_text",
        "is_current",
        "quality_score",
        "career_domain",
        "likely_roles_json",
        "domain_explanation",
        "strengths_json",
        "improvements_json",
        "warnings_json",
        "created_at",
        "updated_at"
    ]
    for col in required_resume_columns:
        assert col in resume_columns, f"Column {col} missing from resumes table schema!"

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "demo@nxtmov.local").first()
        if user:
            assert hasattr(user, "is_email_verified")
            assert hasattr(user, "is_phone_verified")
            assert hasattr(user, "email_verification_token")
            assert hasattr(user, "phone_otp")
            assert hasattr(user, "password_reset_token")

        resumes = db.query(Resume).limit(5).all()
        for r in resumes:
            assert hasattr(r, "career_domain")
            assert hasattr(r, "quality_score")
            assert hasattr(r, "likely_roles_json")
            assert hasattr(r, "domain_explanation")
            assert hasattr(r, "strengths_json")
            assert hasattr(r, "improvements_json")
            assert hasattr(r, "warnings_json")
    finally:
        db.close()


def test_migration_postgresql_legacy_orgrole_and_rbac_upgrade():
    """
    Verifies Alembic migration on a real PostgreSQL database with a legacy orgrole enum type
    and legacy CANDIDATE records, matching the exact Render production failure scenario.
    """
    pg_url_base = os.getenv("TEST_POSTGRES_URL", "postgresql://postgres:vinay@127.0.0.1:5432")
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        conn = psycopg2.connect(f"{pg_url_base}/postgres", connect_timeout=3)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except Exception:
        pytest.skip("PostgreSQL test instance is not reachable; skipping PostgreSQL-specific test.")

    test_db_name = "nxtmov_pg_test_migration"
    test_db_url = f"{pg_url_base}/{test_db_name}"

    try:
        cur = conn.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS {test_db_name};")
        cur.execute(f"CREATE DATABASE {test_db_name};")
        cur.close()
        conn.close()

        cfg = get_test_alembic_config(test_db_url)

        # 1. Upgrade to f1e2d3c4b5a6
        command.upgrade(cfg, "f1e2d3c4b5a6")

        # 2. Setup production state: insert CANDIDATE records and recreate legacy orgrole enum
        pg_conn = psycopg2.connect(test_db_url)
        cur = pg_conn.cursor()
        cur.execute("""
            INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
            VALUES ('vinay_pg@nxtmov.com', 'hash_pwd_pg', 'Vinay Nalavade', true, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id;
        """)
        uid = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO organizations (name, slug, type, owner_id, created_at, updated_at)
            VALUES ('PG Org', 'pg-org', 'INDIVIDUAL', %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id;
        """, (uid,))
        oid = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO organization_memberships (organization_id, user_id, role, created_at, updated_at)
            VALUES (%s, %s, 'CANDIDATE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
        """, (oid, uid))
        cur.execute("""
            INSERT INTO invitations (organization_id, email, role, token, status, expires_at, created_by_user_id, created_at, updated_at)
            VALUES (%s, 'invite_pg@nxtmov.com', 'CANDIDATE', 'tok_pg', 'PENDING', CURRENT_TIMESTAMP, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
        """, (oid, uid))
        pg_conn.commit()

        # Recreate legacy orgrole without MENTOR/STUDENT
        cur.execute("CREATE TYPE orgrole_legacy AS ENUM ('ADMIN', 'RECRUITER', 'CANDIDATE', 'COUNSELOR');")
        cur.execute("ALTER TABLE organization_memberships ALTER COLUMN role TYPE orgrole_legacy USING role::text::orgrole_legacy;")
        cur.execute("ALTER TABLE invitations ALTER COLUMN role TYPE orgrole_legacy USING role::text::orgrole_legacy;")
        cur.execute("DROP TYPE orgrole;")
        cur.execute("ALTER TYPE orgrole_legacy RENAME TO orgrole;")
        pg_conn.commit()
        cur.close()
        pg_conn.close()

        # 3. Upgrade f1e2d3c4b5a6 -> c2d3e4f5a6b7 -> head
        final_rev = run_test_migration_runner(test_db_url)
        assert final_rev == HEAD_REVISION

        # 4. Verify data mapping and new columns
        pg_conn = psycopg2.connect(test_db_url)
        cur = pg_conn.cursor()
        cur.execute("SELECT role FROM organization_memberships WHERE user_id = %s;", (uid,))
        role = cur.fetchone()[0]
        assert role == "STUDENT"

        cur.execute("SELECT role FROM invitations WHERE email = 'invite_pg@nxtmov.com';")
        inv_role = cur.fetchone()[0]
        assert inv_role == "STUDENT"

        cur.execute("SELECT account_type, status FROM users WHERE id = %s;", (uid,))
        acc_type, status = cur.fetchone()
        assert acc_type == "STUDENT"
        assert status == "ACTIVE"

        cur.close()
        pg_conn.close()

        # 5. Verify downgrade and re-upgrade
        command.downgrade(cfg, "f1e2d3c4b5a6")
        command.upgrade(cfg, "head")

    finally:
        try:
            conn2 = psycopg2.connect(f"{pg_url_base}/postgres")
            conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur2 = conn2.cursor()
            cur2.execute(f"DROP DATABASE IF EXISTS {test_db_name};")
            cur2.close()
            conn2.close()
        except Exception:
            pass

