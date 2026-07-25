"""Tests for in-memory conversation context."""

import pytest

from app.chat.context_manager import ContextManager
from app.chat.schemas import ChatIntent


@pytest.mark.asyncio
async def test_creates_updates_and_clears_context() -> None:
    manager = ContextManager()

    empty = await manager.get("conversation")
    updated = await manager.update(
        "conversation",
        user_message="Analise esta imagem",
        assistant_message="Análise concluída",
        intent=ChatIntent.NUTRITION_ANALYSIS,
        module="nutrition_analysis",
        context_updates={"dish": "Arroz"},
    )

    assert empty.messages == []
    assert updated.last_intent is ChatIntent.NUTRITION_ANALYSIS
    assert updated.state == {"dish": "Arroz"}
    assert len(updated.messages) == 2

    await manager.clear("conversation")
    assert (await manager.get("conversation")).messages == []


@pytest.mark.asyncio
async def test_limits_history_and_removes_sensitive_or_image_data() -> None:
    manager = ContextManager(max_messages=3)
    unsafe_updates = {
        "image": "data:image/jpeg;base64,secret",
        "nested": {"data_url": "data:image/jpeg;base64,secret", "safe": True},
    }

    for index in range(2):
        await manager.update(
            "conversation",
            user_message=f"Mensagem {index}",
            assistant_message=f"Resposta {index}",
            intent=ChatIntent.UNKNOWN,
            module="unavailable",
            context_updates=unsafe_updates,
        )

    context = await manager.get("conversation")

    assert len(context.messages) == 3
    assert "image" not in context.state
    assert context.state["nested"] == {"safe": True}
