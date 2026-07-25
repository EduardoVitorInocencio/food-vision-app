"""Integration tests for food analysis endpoints."""

import io

import httpx
import pytest
from PIL import Image

from app.dependencies.services import get_food_analysis_service
from app.main import app
from app.modules.nutrition_analysis.schemas import (
    CalorieRange,
    ConfidenceLevel,
    FoodAnalysis,
    NutritionEstimate,
)
from app.modules.nutrition_analysis.service import FoodAnalysisService
from app.services.image_preprocessor import ImagePreprocessor, PreparedImage


def make_image() -> bytes:
    """Create a valid in-memory PNG fixture."""

    with io.BytesIO() as buffer:
        Image.new("RGB", (100, 50), color="white").save(buffer, format="PNG")
        return buffer.getvalue()


def make_analysis() -> FoodAnalysis:
    """Create a deterministic public analysis result."""

    return FoodAnalysis(
        dish_name="Prato de teste",
        description="Descrição de teste.",
        components=[],
        total_nutrition=NutritionEstimate(calories=250),
        total_calorie_range=CalorieRange(min=220, max=280),
        confidence=ConfidenceLevel.HIGH,
        assumptions=[],
        warnings=[],
        requires_user_confirmation=False,
        follow_up_questions=[],
    )


class StubAnalyzer:
    """Capture prepared images and avoid real OpenAI calls."""

    def __init__(self) -> None:
        """Initialize an empty image capture."""

        self.received_image: PreparedImage | None = None

    async def analyze(self, image: PreparedImage) -> FoodAnalysis:
        """Capture the prepared image and return fixture data."""

        self.received_image = image
        return make_analysis()


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    """Reset FastAPI dependency overrides after each test."""

    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Keep the unversioned health endpoint compatible."""

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_valid_upload_uses_overridden_service() -> None:
    """Route valid uploads through the overridden local service."""

    analyzer = StubAnalyzer()
    service = FoodAnalysisService(ImagePreprocessor(), analyzer)
    app.dependency_overrides[get_food_analysis_service] = lambda: service

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/food-analysis",
            files={"image": ("food.png", make_image(), "image/png")},
        )

    assert response.status_code == 200
    assert response.json()["dish_name"] == "Prato de teste"
    assert analyzer.received_image is not None
    assert analyzer.received_image.data_url.startswith("data:image/jpeg;base64,")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "content_type", "expected_status", "expected_code"),
    [
        (b"", "image/png", 422, "empty_image"),
        (b"text", "text/plain", 415, "unsupported_image_format"),
        (b"corrupted", "image/png", 422, "invalid_image"),
    ],
)
async def test_invalid_uploads_return_consistent_errors(
    content: bytes,
    content_type: str,
    expected_status: int,
    expected_code: str,
) -> None:
    """Map invalid uploads to stable HTTP statuses and error codes."""

    service = FoodAnalysisService(ImagePreprocessor(), StubAnalyzer())
    app.dependency_overrides[get_food_analysis_service] = lambda: service

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/food-analysis",
            files={"image": ("food", content, content_type)},
        )

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code
