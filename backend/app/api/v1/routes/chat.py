"""Chat endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.chat.schemas import ChatResponse
from app.chat.service import ChatService
from app.dependencies.services import get_chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", response_model=ChatResponse)
async def send_chat_message(
    service: Annotated[ChatService, Depends(get_chat_service)],
    message: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
    conversation_id: Annotated[str | None, Form()] = None,
) -> ChatResponse:
    try:
        return await service.send_message(
            message=message,
            image=image,
            conversation_id=conversation_id,
        )
    finally:
        if image is not None:
            await image.close()
