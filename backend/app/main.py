import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings, STATIC_UPLOADS_DIR, init_storage_directories
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=settings.BACKEND_CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

# Global exception handlers ensuring CORS headers and clean JSON responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    headers = dict(getattr(exc, "headers", None) or {})
    origin = request.headers.get("origin")
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"[UNHANDLED SERVER ERROR] Path: {request.url.path}, Error: {exc}", flush=True)
    traceback.print_exc()
    origin = request.headers.get("origin")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Resume processing failed on the server. Please try again."},
        headers=headers,
    )

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

from app.core.migration_runner import run_database_migrations

@app.on_event("startup")
def on_startup():
    init_storage_directories()
    # Execute database migrations (fails loudly if migrations fail)
    run_database_migrations()

    if settings.NXTMOV_DEMO_MODE:
        from app.core.database import SessionLocal
        from app.api.v1.endpoints.auth import ensure_demo_user_exists
        db = SessionLocal()
        try:
            ensure_demo_user_exists(db)
        finally:
            db.close()

# Determine path to frontend static directory & uploads directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
init_storage_directories()

class NoCacheStaticFiles(StaticFiles):
    def is_not_modified(self, response_headers, request_headers) -> bool:
        return False

# Mount uploads directory for persistent user assets
app.mount("/uploads", NoCacheStaticFiles(directory=STATIC_UPLOADS_DIR), name="uploads")

if os.path.exists(FRONTEND_DIR):
    app.mount("/css", NoCacheStaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", NoCacheStaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
    app.mount("/static", NoCacheStaticFiles(directory=FRONTEND_DIR), name="static")

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/static", "/css", "/js", "/uploads")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

@app.get("/", include_in_schema=False)
def read_root():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Welcome to NxtMov API Engine. Visit /api/v1/docs for OpenAPI specifications."}

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav_file = os.path.join(FRONTEND_DIR, "favicon.svg")
    if os.path.exists(fav_file):
        return FileResponse(fav_file, media_type="image/svg+xml")
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
