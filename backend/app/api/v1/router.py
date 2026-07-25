"""Version 1 API router registration."""

from fastapi import APIRouter

from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.food_analysis import router as food_analysis_router

api_v1_router = APIRouter()
api_v1_router.include_router(chat_router)
api_v1_router.include_router(food_analysis_router)
