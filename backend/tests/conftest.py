import pytest
from sqlalchemy import text
from app.core.database import engine, Base
import app.models  # Ensure all models are registered

@pytest.fixture(autouse=True, scope="function")
def reset_db_schema():
    engine.dispose()
    try:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys=OFF;"))
            Base.metadata.drop_all(bind=conn)
            Base.metadata.create_all(bind=conn)
            conn.execute(text("PRAGMA foreign_keys=ON;"))
            conn.commit()
    except Exception:
        Base.metadata.drop_all(bind=engine, check_first=True)
        Base.metadata.create_all(bind=engine, check_first=True)
    yield
    engine.dispose()
