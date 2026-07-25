"""Tests for central chat orchestration."""

import io

import pytest
from fastapi import UploadFile

from app.chat.context_manager import ContextManager
from app.chat.intent_router import IntentRouter
from app.chat.response_builder import ResponseBuilder
from app.chat.schemas import ChatContext, ChatIntent, ModuleResult
from app.chat.service import ChatService
from app.core.exceptions import EmptyChatMessageError


class StubNutritionModule:
    """Track module execution and return deterministic nutrition data."""

    def __init__(self) -> None:
        """Initialize call and context captures."""

        self.calls = 0
        self.context: ChatContext | None = None

    async def execute(
        self,
        *,
        message: str | None,
        image: UploadFile | None,
        context: ChatContext,
    ) -> ModuleResult:
        """Record execution and return a valid module result."""

        self.calls += 1
        self.context = context
        assert image is not None
        return ModuleResult(
            answer="Prato de teste: estimativa total de 250 kcal.",
            intent=ChatIntent.NUTRITION_ANALYSIS,
            module="nutrition_analysis",
            data={"dish_name": "Prato de teste"},
            context_updates={"last_dish": "Prato de teste"},
        )


def make_service(
    module: StubNutritionModule,
    manager: ContextManager,
) -> ChatService:
    """Build a ChatService with local collaborators for unit tests."""

    return ChatService(
        intent_router=IntentRouter(),
        context_manager=manager,
        response_builder=ResponseBuilder(),
        modules={ChatIntent.NUTRITION_ANALYSIS: module},
    )


@pytest.mark.asyncio
async def test_executes_registered_module_and_updates_context() -> None:
    """Execute the registered module and persist its context update."""

    module = StubNutritionModule()
    manager = ContextManager()
    service = make_service(module, manager)
    image = UploadFile(file=io.BytesIO(b"image"), filename="food.jpg")

    response = await service.send_message(
        message="Quantas calorias?",
        image=image,
        conversation_id="existing",
    )

    assert response.conversation_id == "existing"
    assert response.intent is ChatIntent.NUTRITION_ANALYSIS
    assert response.data["dish_name"] == "Prato de teste"
    assert module.calls == 1
    assert (await manager.get("existing")).state["last_dish"] == "Prato de teste"


@pytest.mark.asyncio
async def test_does_not_execute_unregistered_module() -> None:
    """Return unavailable without executing the nutrition module."""

    module = StubNutritionModule()
    manager = ContextManager()
    service = make_service(module, manager)

    response = await service.send_message(
        message="Consulte minha base RAG",
        image=None,
        conversation_id=None,
    )

    assert response.conversation_id
    assert response.intent is ChatIntent.KNOWLEDGE_RAG
    assert response.module == "unavailable"
    assert module.calls == 0


@pytest.mark.asyncio
async def test_rejects_empty_request() -> None:
    """Reject interactions containing neither meaningful text nor image."""

    service = make_service(StubNutritionModule(), ContextManager())

    with pytest.raises(EmptyChatMessageError):
        await service.send_message(
            message=" ",
            image=None,
            conversation_id=None,
        )
