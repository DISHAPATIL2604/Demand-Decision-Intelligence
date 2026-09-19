from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.api import health, auth
from backend.api import demand as demand_api
from backend.db.session import create_tables

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    On startup: create any missing database tables (development convenience).
    For production use Alembic migrations instead.
    """
    logger.info("Starting up — ensuring database tables exist...")
    try:
        create_tables()
        logger.info("Database tables ready.")
    except Exception as exc:
        logger.error("Could not create tables on startup: %s", exc)
    yield
    # (shutdown logic goes here if needed)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register API Routers
# ---------------------------------------------------------------------------
app.include_router(health.router,        prefix=settings.API_V1_STR,                   tags=["Health"])
app.include_router(auth.router,          prefix=f"{settings.API_V1_STR}/auth",          tags=["Auth"])
app.include_router(demand_api.router,    prefix=f"{settings.API_V1_STR}/demand",        tags=["Demand Aggregation"])


@app.get("/")
def root():
    return {
        "message": "Welcome to Demand & Decision Intelligence System API",
        "docs":    f"{settings.API_V1_STR}/docs",
        "health":  f"{settings.API_V1_STR}/health",
        "demand":  f"{settings.API_V1_STR}/demand",
    }

