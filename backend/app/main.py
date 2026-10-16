from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal, ensure_schema_migrations
from app.simulation.building_factory import create_default_campus_building
from app.routers import (
    dashboard_router,
    building_router,
    simulation_router,
    dead_zones_router,
    ml_router,
    optimizer_router,
    alerts_router,
    data_import_router,
    survey_router,
    gateway_router
)
from app.models.gateway import seed_default_students

# Initialize database tables at startup
Base.metadata.create_all(bind=engine)
ensure_schema_migrations()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure default building and demo students exist
    db = SessionLocal()
    try:
        create_default_campus_building(db)
        seed_default_students(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Software Platform for AI-Based Wi-Fi Dead-Zone Detection, Prediction, and AP Placement Optimization",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(building_router, prefix=settings.API_V1_STR)
app.include_router(simulation_router, prefix=settings.API_V1_STR)
app.include_router(dead_zones_router, prefix=settings.API_V1_STR)
app.include_router(ml_router, prefix=settings.API_V1_STR)
app.include_router(optimizer_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(data_import_router, prefix=settings.API_V1_STR)
app.include_router(survey_router, prefix=settings.API_V1_STR)
app.include_router(gateway_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "workflow": "DETECT -> UNDERSTAND -> PREDICT -> OPTIMIZE -> VERIFY"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Wi-Fi Dead-Zone Prediction Backend"}
