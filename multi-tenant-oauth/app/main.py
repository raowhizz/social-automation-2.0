"""
Main FastAPI application for Multi-Tenant OAuth Social Media Automation.
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api import tenants, oauth, accounts, posts, assets, restaurant
from app.models.base import engine, Base
from app.utils.logger import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Social Media Automation - Multi-Tenant OAuth",
    description="Scalable social media automation system for 300+ restaurants using OAuth2",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check endpoints
@app.get("/health")
def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "social-automation-oauth"}


@app.get("/health/db")
def database_health_check():
    """Database health check."""
    try:
        # Try to connect to database
        connection = engine.connect()
        connection.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)},
        )


# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount uploads directory
uploads_dir = Path("uploads/images")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/images", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Include routers
app.include_router(tenants.router)
app.include_router(oauth.router)
app.include_router(accounts.router)
app.include_router(posts.router)
app.include_router(assets.router)
app.include_router(restaurant.router)


# UI Routes
@app.get("/ui")
async def dashboard_ui():
    """Serve the main dashboard UI."""
    static_file = static_dir / "dashboard.html"
    if static_file.exists():
        return FileResponse(static_file)
    return JSONResponse(
        status_code=404,
        content={"detail": "Dashboard UI not found"},
    )


@app.get("/ui/suggestions")
async def suggestions_ui():
    """Serve the post suggestions UI."""
    static_file = static_dir / "post-suggestions.html"
    if static_file.exists():
        return FileResponse(static_file)
    return JSONResponse(
        status_code=404,
        content={"detail": "Post suggestions UI not found"},
    )


@app.get("/ui/create")
async def create_post_ui():
    """Serve the create post UI."""
    static_file = static_dir / "create-post.html"
    if static_file.exists():
        return FileResponse(static_file)
    return JSONResponse(
        status_code=404,
        content={"detail": "Create post UI not found"},
    )


@app.get("/ui/config")
async def config_ui():
    """Serve the restaurant configuration UI."""
    static_file = static_dir / "restaurant-config.html"
    if static_file.exists():
        return FileResponse(static_file)
    return JSONResponse(
        status_code=404,
        content={"detail": "Restaurant config UI not found"},
    )


@app.get("/ui/assets")
async def asset_library_ui():
    """Serve the asset library UI."""
    static_file = static_dir / "asset-library.html"
    if static_file.exists():
        return FileResponse(static_file)
    return JSONResponse(
        status_code=404,
        content={"detail": "Asset library UI not found"},
    )


@app.get("/ui/calendar")
async def content_calendar_ui():
    """Serve the content calendar UI."""
    static_file = static_dir / "calendar.html"
    if static_file.exists():
        return FileResponse(static_file)
    return JSONResponse(
        status_code=404,
        content={"detail": "Content calendar UI not found"},
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("Starting Multi-Tenant OAuth Social Media Automation API")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Debug mode: {os.getenv('DEBUG', 'False')}")

    # Create tables if they don't exist (for development only)
    # In production, use Alembic migrations
    if os.getenv("DEBUG", "False").lower() == "true":
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("Shutting down Multi-Tenant OAuth Social Media Automation API")


# Root endpoint
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Social Media Automation - Multi-Tenant OAuth API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("RELOAD", "True").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
