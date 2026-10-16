from app.routers.dashboard import router as dashboard_router
from app.routers.building import router as building_router
from app.routers.simulation import router as simulation_router
from app.routers.dead_zones import router as dead_zones_router
from app.routers.ml import router as ml_router
from app.routers.optimizer import router as optimizer_router
from app.routers.alerts import router as alerts_router
from app.routers.data_import import router as data_import_router
from app.routers.survey import router as survey_router
from app.routers.gateway import router as gateway_router

__all__ = [
    "dashboard_router",
    "building_router",
    "simulation_router",
    "dead_zones_router",
    "ml_router",
    "optimizer_router",
    "alerts_router",
    "data_import_router",
    "survey_router",
    "gateway_router"
]
