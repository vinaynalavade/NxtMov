import os
import sys
import logging
from sqlalchemy import inspect, text
from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)

INITIAL_REVISION = "ebc0d3f036ab"
HEAD_REVISION = "d3e4f5a6b7c8"


def get_current_alembic_revision(connection) -> str | None:
    """
    Returns the current revision recorded in alembic_version table, or None if table/row missing.
    """
    inspector = inspect(connection)
    if not inspector.has_table("alembic_version"):
        return None
    try:
        result = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
        return result
    except Exception:
        return None


def has_existing_app_schema(connection) -> bool:
    """
    Checks if initial core application tables (e.g. users, organizations) exist in the database.
    """
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    return "users" in existing_tables or "organizations" in existing_tables


def sanitize_db_url(url: str) -> str:
    """
    Sanitizes database URL for safe logging without exposing passwords.
    """
    if not url:
        return ""
    if "@" in url:
        prefix, rest = url.split("@", 1)
        scheme = prefix.split("://")[0]
        return f"{scheme}://****:****@{rest}"
    return url


def run_database_migrations() -> None:
    """
    Production-safe database migration bootstrap.
    1. Connects to database and inspects schema state.
    2. If existing schema exists without alembic_version, stamps baseline ebc0d3f036ab.
    3. Runs alembic upgrade to head (a1b2c3d4e5f6).
    4. Verifies head revision was reached.
    5. Fails loudly on any error so startup does not falsely report live status.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")
    alembic_dir_path = os.path.join(backend_dir, "alembic")

    if not os.path.exists(alembic_ini_path) or not os.path.exists(alembic_dir_path):
        err_msg = f"[DB MIGRATION ERROR] Alembic configuration not found at {alembic_ini_path}"
        print(err_msg, flush=True)
        raise RuntimeError(err_msg)

    redacted_url = sanitize_db_url(settings.DATABASE_URL)
    print(f"[DB MIGRATION] Database URL configured: {redacted_url}", flush=True)
    print("[DB MIGRATION] Checking migration state", flush=True)

    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", alembic_dir_path)
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    with engine.connect() as connection:
        current_rev = get_current_alembic_revision(connection)
        has_schema = has_existing_app_schema(connection)

        print(f"[DB MIGRATION] Existing schema detected: {str(has_schema).lower()}", flush=True)
        print(f"[DB MIGRATION] Current Alembic revision: {current_rev}", flush=True)

        if current_rev is None and has_schema:
            print(f"[DB MIGRATION] Establishing baseline: {INITIAL_REVISION}", flush=True)
            command.stamp(alembic_cfg, INITIAL_REVISION)

    print("[DB MIGRATION] Applying migrations to head", flush=True)
    command.upgrade(alembic_cfg, "head")

    with engine.connect() as connection:
        final_rev = get_current_alembic_revision(connection)
        print(f"[DB MIGRATION] Final Alembic revision: {final_rev}", flush=True)

    if final_rev != HEAD_REVISION:
        err_msg = (
            f"[DB MIGRATION ERROR] Migration did not reach expected head revision {HEAD_REVISION}! "
            f"Current revision is {final_rev}."
        )
        print(err_msg, flush=True)
        raise RuntimeError(err_msg)

    print("[DB MIGRATION] Migration completed successfully", flush=True)
