"""API router registration."""

from fastapi import APIRouter

from app.api.routes.food_analysis import router as food_analysis_router

api_router = APIRouter()
api_router.include_router(food_analysis_router)
