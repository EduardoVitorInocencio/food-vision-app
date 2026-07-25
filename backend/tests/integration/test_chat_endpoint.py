"""Integration tests for the chat endpoint."""

import io
from collections.abc import Generator

import httpx
import pytest
from fastapi import UploadFile

from app.chat.context_manager import ContextManager
from app.chat.intent_router import IntentRouter
from app.chat.response_builder import ResponseBuilder
from app.chat.schemas import ChatContext, ChatIntent, ModuleResult
from app.chat.service import ChatService
from app.dependencies.services import get_chat_service
from app.main import app


class StubNutritionModule:
    """Record chat route inputs without invoking external services."""

    def __init__(self) -> None:
        """Initialize empty input captures."""

        self.received_message: str | None = None
        self.received_image: UploadFile | None = None

    async def execute(
        self,
        *,
        message: str | None,
        image: UploadFile | None,
        context: ChatContext,
    ) -> ModuleResult:
        """Capture module inputs and return a deterministic result."""

        del context
        self.received_message = message
        self.received_image = image
        return ModuleResult(
            answer="Análise concluída.",
            intent=ChatIntent.NUTRITION_ANALYSIS,
            module="nutrition_analysis",
            data={"dish_name": "Prato de teste"},
        )


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None]:
    """Reset FastAPI dependency overrides after each test."""

    yield
    app.dependency_overrides.clear()


def override_chat_service(module: StubNutritionModule) -> None:
    """Install a fully local ChatService dependency override."""

    service = ChatService(
        intent_router=IntentRouter(),
        context_manager=ContextManager(),
        response_builder=ResponseBuilder(),
        modules={ChatIntent.NUTRITION_ANALYSIS: module},
    )
    app.dependency_overrides[get_chat_service] = lambda: service


@pytest.mark.asyncio
@pytest.mark.parametrize("message", [None, "Quantas calorias tem este prato?"])
async def test_accepts_image_with_optional_message(message: str | None) -> None:
    """Accept an image alone or accompanied by text and close its upload."""

    module = StubNutritionModule()
    override_chat_service(module)
    data = {"message": message} if message else {}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/chat/messages",
            data=data,
            files={"image": ("food.png", io.BytesIO(b"image"), "image/png")},
        )

    assert response.status_code == 200
    assert response.json()["intent"] == "nutrition_analysis"
    assert response.json()["role"] == "assistant"
    assert module.received_message == message
    assert module.received_image is not None
    assert module.received_image.file.closed


@pytest.mark.asyncio
async def test_rejects_request_without_message_or_image() -> None:
    """Return the controlled 422 error when both conditional fields are absent."""

    override_chat_service(StubNutritionModule())

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/v1/chat/messages")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "empty_chat_message"
