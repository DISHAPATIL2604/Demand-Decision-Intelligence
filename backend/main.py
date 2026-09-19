from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.api import health, auth, demand, products, upload, forecast, inventory, analytics

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(
    health.router,
    prefix=settings.API_V1_STR,
    tags=["Health"]
)

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Auth"]
)

app.include_router(
    demand.router,
    prefix=f"{settings.API_V1_STR}/demand",
    tags=["Demand Intelligence"]
)

app.include_router(
    products.router,
    prefix=f"{settings.API_V1_STR}/products",
    tags=["Products"]
)

app.include_router(
    upload.router,
    prefix=f"{settings.API_V1_STR}/upload",
    tags=["Data Upload"]
)

app.include_router(
    forecast.router,
    prefix=f"{settings.API_V1_STR}/forecast",
    tags=["Forecasting Suite"]
)

app.include_router(
    inventory.router,
    prefix=f"{settings.API_V1_STR}/inventory",
    tags=["Inventory Optimization"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_STR}/analytics",
    tags=["Business Analytics"]
)


@app.get("/")
def root():
    return {
        "message": "Welcome to Demand & Decision Intelligence System API",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health"
    }