"""Tests for public food analysis schemas."""

import math

import pytest
from pydantic import ValidationError

from app.modules.nutrition_analysis.schemas import (
    CalorieRange,
    ConfidenceLevel,
    FoodAnalysis,
    NutritionEstimate,
)


def test_schema_serializes_public_contract() -> None:
    """Serialize enums and numeric fields through the public contract."""

    analysis = FoodAnalysis(
        dish_name="Fruta",
        description="Uma fruta.",
        components=[],
        total_nutrition=NutritionEstimate(calories=80),
        total_calorie_range=CalorieRange(min=70, max=90),
        confidence=ConfidenceLevel.HIGH,
        assumptions=[],
        warnings=[],
        requires_user_confirmation=False,
        follow_up_questions=[],
    )

    assert analysis.model_dump(mode="json")["confidence"] == "high"
    assert analysis.model_dump(mode="json")["total_calorie_range"] == {
        "min": 70.0,
        "max": 90.0,
    }


def test_calorie_range_rejects_inverted_values() -> None:
    """Reject a calorie range whose minimum exceeds its maximum."""

    with pytest.raises(ValidationError):
        CalorieRange(min=500, max=100)


def test_nutrition_rejects_non_finite_values() -> None:
    """Reject infinite nutritional estimates."""

    with pytest.raises(ValidationError):
        NutritionEstimate(calories=math.inf)


def test_analysis_rejects_total_calories_outside_range() -> None:
    """Reject totals that fall outside the declared calorie range."""

    with pytest.raises(ValidationError):
        FoodAnalysis(
            dish_name="Inconsistente",
            description="Teste.",
            components=[],
            total_nutrition=NutritionEstimate(calories=900),
            total_calorie_range=CalorieRange(min=100, max=200),
            confidence=ConfidenceLevel.LOW,
            assumptions=[],
            warnings=[],
            requires_user_confirmation=True,
            follow_up_questions=[],
        )
