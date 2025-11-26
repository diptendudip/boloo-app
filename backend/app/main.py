"""
Main FastAPI application with security enhancements
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging
import time
import os

from app.config import settings
from app.database import engine, Base
from app.routers import auth, cases, entities, taxonomies, admin, monitoring, monitoring_v2, triage, transcription, next_steps, users, chat, feed, location, dropdown, health  # , uploads  # TODO: Fix CaseAttachment model
# Disabled heavy ML: from app.routers import knowledge  # Requires 1.2GB+ RAM (sentence-transformers + PyTorch + FAISS)

# SECURITY FIX #1 & #4: Import security middleware
from app.middleware.security import HTTPSRedirectMiddleware, SecurityHeadersMiddleware
from app.middleware.rate_limit import limiter
from app.utils.security_logger import security_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} API...")
    logger.info(f"Environment: {settings.APP_ENV}")

    # Create tables (for development; use Alembic in production)
    if settings.DEBUG:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)

    yield

    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Conversational AI Citizen Reporting Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# SECURITY FIX #1: Add HTTPS enforcement in production
if settings.is_production:
    app.add_middleware(
        HTTPSRedirectMiddleware,
        enabled=True
    )
    logger.info("✅ HTTPS enforcement enabled (production mode)")

# SECURITY FIX #1: Add security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    enabled=settings.is_production,  # Enable in production, optional in dev
    hsts_max_age=31536000  # 1 year
)
logger.info(f"✅ Security headers middleware enabled (production: {settings.is_production})")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SECURITY FIX #4: Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.3f}s with status {response.status_code}"
    )

    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
# Health check endpoints (no prefix for backward compatibility)
app.include_router(health.router)

app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(cases.router, prefix="/v1/cases", tags=["Cases"])
app.include_router(triage.router, prefix="/v1/cases", tags=["Triage"])
app.include_router(transcription.router, prefix="/v1/transcription", tags=["Transcription"])
app.include_router(next_steps.router, prefix="/v1", tags=["Next Steps"])
app.include_router(entities.router, prefix="/v1/entities", tags=["Entities"])
app.include_router(taxonomies.router, prefix="/v1/taxonomies", tags=["Taxonomies"])
app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])
app.include_router(monitoring.router, prefix="/v1/monitoring", tags=["Monitoring"])
app.include_router(monitoring_v2.router, prefix="/v1/monitoring", tags=["Monitoring v2"])
app.include_router(users.router, tags=["Users"])
app.include_router(chat.router)
app.include_router(feed.router, prefix="/v1/feed", tags=["Feed"])
# Disabled for B1 tier (OOM): app.include_router(knowledge.router)  # Knowledge base / RAG endpoints - Requires B2+ tier (1.2GB+ ML models)
app.include_router(location.router)  # Location detection and validation
app.include_router(dropdown.router)  # Cascading dropdown for address selection
# app.include_router(uploads.router, prefix="/v1/uploads", tags=["Uploads"])  # TODO: Fix CaseAttachment model


# Mount static files for mobile web app
# Serves React Native Web build from /mobile path
static_mobile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "mobile")
if os.path.exists(static_mobile_path):
    app.mount("/mobile", StaticFiles(directory=static_mobile_path, html=True), name="mobile")
    logger.info(f"✅ Mobile web app mounted at /mobile (serving from {static_mobile_path})")
else:
    logger.warning(f"⚠️  Mobile web static files not found at {static_mobile_path}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
