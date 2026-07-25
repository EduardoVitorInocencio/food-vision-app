"""Replaceable in-memory conversation context."""

import asyncio
from copy import deepcopy
from typing import Any

from app.chat.schemas import ChatContext, ChatIntent, ContextMessage

_BLOCKED_CONTEXT_KEYS = ("api_key", "base64", "client", "data_url", "image", "upload")


class ContextManager:
    """Stores bounded context that is lost when the application restarts."""

    def __init__(self, max_messages: int = 20) -> None:
        """Initialize an empty process-local store with a history limit."""

        if max_messages < 1:
            raise ValueError("max_messages deve ser maior que zero.")
        self._max_messages = max_messages
        self._contexts: dict[str, ChatContext] = {}
        # One lock protects both creation and mutation so concurrent requests
        # cannot overwrite the same process-local conversation.
        self._lock = asyncio.Lock()

    async def get(self, conversation_id: str) -> ChatContext:
        """Return an isolated copy of a conversation, creating it if absent."""

        async with self._lock:
            context = self._contexts.get(conversation_id)
            if context is None:
                context = ChatContext(conversation_id=conversation_id)
                self._contexts[conversation_id] = context
            # Callers receive a snapshot and cannot mutate shared state after
            # the lock is released.
            return context.model_copy(deep=True)

    async def update(
        self,
        conversation_id: str,
        *,
        user_message: str | None,
        assistant_message: str,
        intent: ChatIntent,
        module: str,
        context_updates: dict[str, Any] | None = None,
    ) -> ChatContext:
        """Append bounded history and merge sanitized module state."""

        async with self._lock:
            context = self._contexts.setdefault(
                conversation_id,
                ChatContext(conversation_id=conversation_id),
            )
            context.messages.append(
                ContextMessage(role="user", content=user_message or "[imagem enviada]")
            )
            context.messages.append(
                ContextMessage(role="assistant", content=assistant_message)
            )
            # The bound counts both user and assistant entries, not turns.
            context.messages = context.messages[-self._max_messages :]
            context.last_intent = intent
            context.last_module = module
            if context_updates:
                # Sanitize before merging because module results may contain
                # nested values that are unsafe or too large to retain.
                context.state.update(_sanitize_mapping(context_updates))
            return context.model_copy(deep=True)

    async def clear(self, conversation_id: str) -> None:
        """Remove one conversation from process memory."""

        async with self._lock:
            self._contexts.pop(conversation_id, None)

    async def clear_all(self) -> None:
        """Remove every in-memory conversation during application shutdown."""

        async with self._lock:
            self._contexts.clear()


def _sanitize_mapping(values: dict[str, Any]) -> dict[str, Any]:
    """Remove context keys that could retain uploads, secrets, or image data."""

    sanitized: dict[str, Any] = {}
    for key, value in values.items():
        normalized_key = key.lower()
        # Substring matching also blocks derived names such as
        # "original_image_data_url" without maintaining an exhaustive list.
        if any(blocked in normalized_key for blocked in _BLOCKED_CONTEXT_KEYS):
            continue
        sanitized[key] = _sanitize_value(value)
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _sanitize_mapping(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_value(item) for item in value)
    return deepcopy(value)
