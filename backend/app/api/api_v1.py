"""API Version 1 root router mounting versioned endpoints."""

from fastapi import APIRouter
from backend.app.api.routes.analytics import router as analytics_router
from backend.app.api.routes.datasets import router as datasets_router
from backend.app.api.routes.evaluation import router as evaluation_router
from backend.app.api.routes.health import router as health_router

api_v1_router = APIRouter()

# Core system endpoints
api_v1_router.include_router(health_router)

# Ingestion & Dataset pipeline endpoints
api_v1_router.include_router(datasets_router)

# Analytics & Cricket Metrics Engine endpoints
api_v1_router.include_router(analytics_router)

# Role Classification & Evaluation Framework endpoints
api_v1_router.include_router(evaluation_router)

# Future module routes (To be registered in their respective development phases):
# - api_v1_router.include_router(players_router, prefix="/players", tags=["Players"])
# - api_v1_router.include_router(matches_router, prefix="/matches", tags=["Matches"])
# - api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
# - api_v1_router.include_router(evaluation_router, prefix="/evaluations", tags=["Evaluation"])
# - api_v1_router.include_router(rankings_router, prefix="/rankings", tags=["Rankings"])
# - api_v1_router.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])
