import os
from typing import List, Union, Optional, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NxtMov API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Secret Key for JWT Signing
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nxtmov_super_secret_dev_key_change_in_production_123456789")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 Days

    # Temporary Development & Demo Credentials (REMOVE BEFORE PRODUCTION DEPLOYMENT)
    NXTMOV_DEMO_MODE: bool = os.getenv("NXTMOV_DEMO_MODE", "true").lower() in ("true", "1", "yes")
    DEMO_USER_EMAIL: str = "demo@nxtmov.local"
    DEMO_USER_PASSWORD: str = "NxtMov@123"

    # Application Frontend Base URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://vinaynalavade.github.io/NxtMov")

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
        "http://localhost:5502",
        "http://127.0.0.1:5502",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://vinaynalavade.github.io",
    ]

    # Regex pattern for dynamic local development ports on localhost and 127.0.0.1
    BACKEND_CORS_ORIGIN_REGEX: Optional[str] = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple, set)):
            return [str(i).strip() for i in v if str(i).strip()]
        return v

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nxtmov.db")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

# Unified Storage Architecture
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_UPLOADS_DIR = os.path.join(APP_DIR, "static_uploads")
AVATAR_STORAGE_DIR = os.path.join(STATIC_UPLOADS_DIR, "avatars")
RESUME_STORAGE_DIR = os.path.join(STATIC_UPLOADS_DIR, "resumes")

def init_storage_directories():
    os.makedirs(STATIC_UPLOADS_DIR, exist_ok=True)
    os.makedirs(AVATAR_STORAGE_DIR, exist_ok=True)
    os.makedirs(RESUME_STORAGE_DIR, exist_ok=True)
