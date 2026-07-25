"""Tests for uniform chat responses."""

from app.chat.response_builder import ResponseBuilder
from app.chat.schemas import ChatIntent, ModuleResult


def test_converts_module_result_and_generates_identifiers() -> None:
    """Convert module data and generate conversation/message identifiers."""

    builder = ResponseBuilder()
    conversation_id = builder.ensure_conversation_id(None)
    result = ModuleResult(
        answer="Análise concluída.",
        intent=ChatIntent.NUTRITION_ANALYSIS,
        module="nutrition_analysis",
        data={"calories": 250},
    )

    response = builder.from_module(conversation_id, result)

    assert response.conversation_id == conversation_id
    assert response.message_id
    assert response.data == {"calories": 250}
    assert response.role == "assistant"


def test_builds_unavailable_module_response() -> None:
    """Build a stable response for a recognized unavailable module."""

    response = ResponseBuilder().unavailable(
        "conversation",
        ChatIntent.MEAL_COMPARISON,
    )

    assert response.intent is ChatIntent.MEAL_COMPARISON
    assert response.module == "unavailable"
    assert response.data == {}
    assert "ainda não está disponível" in response.answer
