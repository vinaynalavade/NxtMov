from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", summary="API Health Check")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": "development"
    }
