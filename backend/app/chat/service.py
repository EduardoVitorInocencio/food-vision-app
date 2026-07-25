"""Central chat orchestration service."""

from typing import Protocol

from fastapi import UploadFile

from app.chat.context_manager import ContextManager
from app.chat.intent_router import IntentRouter
from app.chat.response_builder import ResponseBuilder
from app.chat.schemas import ChatContext, ChatIntent, ChatResponse, ModuleResult
from app.core.exceptions import EmptyChatMessageError


class ChatModule(Protocol):
    async def execute(
        self,
        *,
        message: str | None,
        image: UploadFile | None,
        context: ChatContext,
    ) -> ModuleResult: ...


class ChatService:
    def __init__(
        self,
        *,
        intent_router: IntentRouter,
        context_manager: ContextManager,
        response_builder: ResponseBuilder,
        modules: dict[ChatIntent, ChatModule],
    ) -> None:
        self.intent_router = intent_router
        self.context_manager = context_manager
        self.response_builder = response_builder
        self.modules = modules

    async def send_message(
        self,
        *,
        message: str | None,
        image: UploadFile | None,
        conversation_id: str | None,
    ) -> ChatResponse:
        normalized_message = message.strip() if message else None
        if not normalized_message and image is None:
            raise EmptyChatMessageError

        current_id = self.response_builder.ensure_conversation_id(conversation_id)
        context = await self.context_manager.get(current_id)
        intent = await self.intent_router.detect(
            normalized_message,
            has_image=image is not None,
            available_modules=set(self.modules),
        )
        module = self.modules.get(intent)

        context_updates: dict[str, object] = {}
        if module is not None:
            result = await module.execute(
                message=normalized_message,
                image=image,
                context=context,
            )
            response = self.response_builder.from_module(current_id, result)
            context_updates = result.context_updates
        elif intent is ChatIntent.UNKNOWN:
            response = self.response_builder.unknown(current_id)
        else:
            response = self.response_builder.unavailable(current_id, intent)

        await self.context_manager.update(
            current_id,
            user_message=normalized_message,
            assistant_message=response.answer,
            intent=response.intent,
            module=response.module,
            context_updates=context_updates,
        )
        return response
