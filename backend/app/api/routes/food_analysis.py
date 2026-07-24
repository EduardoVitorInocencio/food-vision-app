"""Food analysis routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies.services import get_food_analysis_service
from app.schemas.food_analysis import FoodAnalysis
from app.services.food_analysis_service import FoodAnalysisService

router = APIRouter(tags=["food-analysis"])


@router.post("/food-analysis", response_model=FoodAnalysis)
async def analyze_food(
    image: Annotated[
        UploadFile,
        File(description="Imagem JPEG, PNG ou WebP do prato."),
    ],
    service: Annotated[
        FoodAnalysisService,
        Depends(get_food_analysis_service),
    ],
) -> FoodAnalysis:
    try:
        return await service.analyze(image)
    finally:
        await image.close()
