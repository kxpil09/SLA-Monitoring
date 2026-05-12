"""
main.py — FastAPI application entry point.

FIXES:
  - FIX: Added loud warning that create_all() is dev-only and must be replaced
    by Alembic migrations before going to production. Silently running
    create_all() in prod gives false confidence and won't apply schema changes.
"""

import logging
import logging.config

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import router
from app.alert_routes import router as alert_router


# -----------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": settings.LOG_LEVEL,
    },
})

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# App lifespan (startup / shutdown hooks)
# -----------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SLA Monitor (env=%s)", settings.APP_ENV)
    
    # Run database migrations on startup
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
    
    logger.info("Application startup complete.")
    yield
    logger.info("Shutting down SLA Monitor")


# -----------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------

app = FastAPI(
    title="SLA Monitor",
    description=(
        "Monitors external services for uptime and latency. "
        "Celery Beat pings registered URLs every 2 minutes and stores results."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://sla-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(alert_router)


# -----------------------------------------------------------------------
# Health check endpoint
# -----------------------------------------------------------------------

@app.get("/health", tags=["meta"])
def health():
    """Liveness probe. Returns 200 if the app process is running."""
    return {"status": "ok"}