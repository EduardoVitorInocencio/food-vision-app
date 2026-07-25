"""Tests for food analysis service."""

import io
from unittest.mock import AsyncMock

import pytest
from fastapi import UploadFile

from app.modules.nutrition_analysis.schemas import (
    CalorieRange,
    ConfidenceLevel,
    FoodAnalysis,
    NutritionEstimate,
)
from app.modules.nutrition_analysis.service import FoodAnalysisService
from app.services.image_preprocessor import PreparedImage


def make_analysis() -> FoodAnalysis:
    return FoodAnalysis(
        dish_name="Arroz",
        description="Porção de arroz.",
        components=[],
        total_nutrition=NutritionEstimate(calories=200),
        total_calorie_range=CalorieRange(min=180, max=220),
        confidence=ConfidenceLevel.HIGH,
        assumptions=[],
        warnings=[],
        requires_user_confirmation=False,
        follow_up_questions=[],
    )


@pytest.mark.asyncio
async def test_service_orchestrates_preprocessor_and_analyzer() -> None:
    prepared = PreparedImage(
        data_url="data:image/jpeg;base64,ZmFrZQ==",
        width=100,
        height=50,
        original_size_bytes=10,
    )
    expected = make_analysis()
    preprocessor = AsyncMock()
    preprocessor.prepare.return_value = prepared
    analyzer = AsyncMock()
    analyzer.analyze.return_value = expected
    service = FoodAnalysisService(preprocessor, analyzer)
    upload = UploadFile(file=io.BytesIO(b"image"), filename="food.jpg")

    result = await service.analyze(upload)

    assert result == expected
    preprocessor.prepare.assert_awaited_once_with(upload)
    analyzer.analyze.assert_awaited_once_with(prepared)
