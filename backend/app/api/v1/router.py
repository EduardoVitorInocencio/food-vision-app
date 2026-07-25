"""Version 1 API router registration."""

from fastapi import APIRouter

from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.food_analysis import router as food_analysis_router

api_v1_router = APIRouter()
# Keep versioned capabilities grouped here so the public prefix only changes
# in one place when new v1 routes are added.
api_v1_router.include_router(chat_router)
# Preserve the compatibility endpoint alongside the newer chat surface.
api_v1_router.include_router(food_analysis_router)
