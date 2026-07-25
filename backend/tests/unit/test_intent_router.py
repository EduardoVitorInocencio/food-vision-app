"""Tests for deterministic intent routing."""

import pytest

from app.chat.intent_router import IntentRouter
from app.chat.schemas import ChatIntent


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("message", "has_image", "expected"),
    [
        (None, True, ChatIntent.NUTRITION_ANALYSIS),
        ("Quantas calorias tem este prato?", True, ChatIntent.NUTRITION_ANALYSIS),
        ("Qual é a quantidade de proteína?", True, ChatIntent.NUTRITION_ANALYSIS),
        ("Converse comigo", False, ChatIntent.UNKNOWN),
        ("Consulte minha base RAG", False, ChatIntent.KNOWLEDGE_RAG),
        ("Compare esta refeição com a anterior", True, ChatIntent.MEAL_COMPARISON),
        ("Analise os possíveis alérgenos", True, ChatIntent.ALLERGEN_ANALYSIS),
    ],
)
async def test_detects_supported_and_unavailable_intents(
    message: str | None,
    has_image: bool,
    expected: ChatIntent,
) -> None:
    router = IntentRouter()

    result = await router.detect(
        message,
        has_image,
        {ChatIntent.NUTRITION_ANALYSIS},
    )

    assert result is expected
