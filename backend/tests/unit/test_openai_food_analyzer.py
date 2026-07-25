"""Tests for the OpenAI food analyzer."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import APIConnectionError

from app.core.exceptions import (
    InvalidOpenAIResponseError,
    OpenAIUnavailableError,
)
from app.modules.nutrition_analysis.analyzer import OpenAIFoodAnalyzer
from app.modules.nutrition_analysis.schemas import (
    CalorieRange,
    ConfidenceLevel,
    FoodAnalysis,
    NutritionEstimate,
)
from app.services.image_preprocessor import PreparedImage


def make_analysis() -> FoodAnalysis:
    """Create a structured analysis fixture."""

    return FoodAnalysis(
        dish_name="Salada",
        description="Salada simples.",
        components=[],
        total_nutrition=NutritionEstimate(calories=100),
        total_calorie_range=CalorieRange(min=80, max=120),
        confidence=ConfidenceLevel.MEDIUM,
        assumptions=[],
        warnings=[],
        requires_user_confirmation=False,
        follow_up_questions=[],
    )


def make_image() -> PreparedImage:
    """Create a prepared image fixture without real image bytes."""

    return PreparedImage(
        data_url="data:image/jpeg;base64,ZmFrZQ==",
        width=100,
        height=100,
        original_size_bytes=10,
    )


@pytest.mark.asyncio
async def test_analyzer_returns_structured_response() -> None:
    """Return parsed output and send the expected multimodal contract."""

    expected = make_analysis()
    parse = AsyncMock(
        return_value=SimpleNamespace(
            output_parsed=expected,
            id="resp_test",
        )
    )
    client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    analyzer = OpenAIFoodAnalyzer(client=client, model="gpt-4o-mini")

    result = await analyzer.analyze(make_image())

    assert result == expected
    kwargs = parse.await_args.kwargs
    assert kwargs["text_format"] is FoodAnalysis
    assert kwargs["input"][1]["content"][1] == {
        "type": "input_image",
        "image_url": "data:image/jpeg;base64,ZmFrZQ==",
        "detail": "auto",
    }


@pytest.mark.asyncio
async def test_analyzer_rejects_missing_output_parsed() -> None:
    """Reject a response without Structured Output."""

    parse = AsyncMock(return_value=SimpleNamespace(output_parsed=None, id="resp_empty"))
    client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    analyzer = OpenAIFoodAnalyzer(client=client, model="gpt-4o-mini")

    with pytest.raises(InvalidOpenAIResponseError):
        await analyzer.analyze(make_image())


@pytest.mark.asyncio
async def test_analyzer_maps_connection_error() -> None:
    """Map SDK connection failures to the public unavailable error."""

    error = APIConnectionError(
        request=httpx.Request(
            "POST",
            "https://api.openai.com/v1/responses",
        )
    )
    parse = AsyncMock(side_effect=error)
    client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    analyzer = OpenAIFoodAnalyzer(client=client, model="gpt-4o-mini")

    with pytest.raises(OpenAIUnavailableError) as exc_info:
        await analyzer.analyze(make_image())

    assert exc_info.value.__cause__ is error
