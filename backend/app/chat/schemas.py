"""Shared chat contracts."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatSchema(BaseModel):
    """Strict base model for chat contracts."""

    model_config = ConfigDict(extra="forbid")


class ChatIntent(StrEnum):
    """Intent values exposed by the chat contract."""

    NUTRITION_ANALYSIS = "nutrition_analysis"
    FOOD_IDENTIFICATION = "food_identification"
    ALLERGEN_ANALYSIS = "allergen_analysis"
    MEAL_COMPARISON = "meal_comparison"
    KNOWLEDGE_RAG = "knowledge_rag"
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"


class ModuleResult(ChatSchema):
    """Internal result returned by a registered chat module."""

    answer: str
    intent: ChatIntent
    module: str
    data: dict[str, Any] = Field(default_factory=dict)
    context_updates: dict[str, Any] = Field(default_factory=dict)
    suggested_actions: list[str] = Field(default_factory=list)


class ChatResponse(ChatSchema):
    """Uniform assistant response returned to API clients."""

    conversation_id: str
    message_id: str
    role: Literal["assistant"] = "assistant"
    answer: str
    intent: ChatIntent
    module: str
    data: dict[str, Any] = Field(default_factory=dict)
    suggested_actions: list[str] = Field(default_factory=list)


class ContextMessage(ChatSchema):
    """Minimal message stored in the temporary conversation history."""

    role: Literal["user", "assistant"]
    content: str


class ChatContext(ChatSchema):
    """Serializable in-memory state for one conversation."""

    conversation_id: str
    messages: list[ContextMessage] = Field(default_factory=list)
    last_intent: ChatIntent | None = None
    last_module: str | None = None
    state: dict[str, Any] = Field(default_factory=dict)
