"""
FastAPI application entry point for Demand & Decision Intelligence System.
On startup, ensures database tables exist and seeds the default roles.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.core.config import settings
from backend.api import health, auth, demand, products, upload, forecast, inventory, analytics, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables + seed roles. Shutdown: nothing extra."""
    from backend.db.session import engine, Base, SessionLocal
    from backend.models import Role  # noqa – triggers model registration

    # 1. Create all tables that don't exist yet (safe, non-destructive)
    Base.metadata.create_all(bind=engine)

    # 2. Seed the three standard roles
    db = SessionLocal()
    try:
        default_roles = [
            {"id": 1, "name": "admin",   "description": "System Administrator with full management access"},
            {"id": 2, "name": "manager", "description": "Store and Inventory Manager with operational access"},
            {"id": 3, "name": "viewer",  "description": "Read-only analyst viewer"},
        ]
        for r_info in default_roles:
            if not db.query(Role).filter(Role.name == r_info["name"]).first():
                db.add(Role(**r_info))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[WARN] Could not seed roles: {e}")
    finally:
        db.close()

    yield  # application runs here


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)

# Custom observability & timing middleware
app.add_middleware(ObservabilityMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router,     prefix=settings.API_V1_STR,              tags=["Health"])
app.include_router(auth.router,       prefix=f"{settings.API_V1_STR}/auth",     tags=["Auth"])
app.include_router(demand.router,     prefix=f"{settings.API_V1_STR}/demand",   tags=["Demand Intelligence"])
app.include_router(products.router,   prefix=f"{settings.API_V1_STR}/products", tags=["Products"])
app.include_router(upload.router,     prefix=f"{settings.API_V1_STR}/upload",   tags=["Data Upload"])
app.include_router(forecast.router,   prefix=f"{settings.API_V1_STR}/forecast", tags=["Forecasting Suite"])
app.include_router(inventory.router,  prefix=f"{settings.API_V1_STR}/inventory",tags=["Inventory Optimization"])
app.include_router(analytics.router,  prefix=f"{settings.API_V1_STR}/analytics",tags=["Business Analytics & Anomalies"])
app.include_router(chat.router,       prefix=f"{settings.API_V1_STR}/chat",     tags=["AI Assistant"])

app.include_router(
    market_prices.router,
    prefix=f"{settings.API_V1_STR}/market-prices",
    tags=["Government Market Prices & Stocking Intelligence"]
)

app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["AI Decision Assistant"]
)

@app.get("/")
def root():
    return {
        "message": "Welcome to Demand & Decision Intelligence System API",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
    }