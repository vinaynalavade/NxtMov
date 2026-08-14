import os
from typing import List, Union
from pydantic import AnyHttpUrl, validator
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

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://vinaynalavade.github.io",
]

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nxtmov.db")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
