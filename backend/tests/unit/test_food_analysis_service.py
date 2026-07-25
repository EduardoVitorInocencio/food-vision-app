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
from app.modules.nutrition_analysis.service import (
    FoodAnalysisService,
    NutritionAnalysisModule,
)
from app.services.image_preprocessor import PreparedImage


def make_analysis() -> FoodAnalysis:
    """Create a deterministic nutrition analysis fixture."""

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
    """Pass the prepared image from preprocessor to analyzer exactly once."""

    # Mock the two ports so the test only verifies orchestration and handoff.
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


@pytest.mark.asyncio
async def test_chat_adapter_reuses_food_analysis_service() -> None:
    """Reuse service output for chat data, context, and answer text."""

    analysis = make_analysis()
    service = AsyncMock()
    service.analyze.return_value = analysis
    module = NutritionAnalysisModule(service)
    # Build the same upload object a route would hand to the adapter.
    upload = UploadFile(file=io.BytesIO(b"image"), filename="food.jpg")

    result = await module.execute(
        message="Quantas calorias?",
        image=upload,
        context=AsyncMock(),
    )

    assert result.data == analysis.model_dump(mode="json")
    assert result.context_updates["last_nutrition_analysis"] == result.data
    assert "200 kcal" in result.answer
    service.analyze.assert_awaited_once_with(upload)
