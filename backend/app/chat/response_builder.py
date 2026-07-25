"""Uniform chat response construction."""

from uuid import uuid4

from app.chat.schemas import ChatIntent, ChatResponse, ModuleResult

_UNAVAILABLE_MESSAGES = {
    ChatIntent.FOOD_IDENTIFICATION: (
        "O módulo de identificação de alimentos ainda não está disponível."
    ),
    ChatIntent.ALLERGEN_ANALYSIS: (
        "O módulo de análise de alérgenos ainda não está disponível."
    ),
    ChatIntent.MEAL_COMPARISON: (
        "O módulo de comparação de refeições ainda não está disponível."
    ),
    ChatIntent.KNOWLEDGE_RAG: (
        "O módulo de consulta à base de conhecimento ainda não está disponível."
    ),
    ChatIntent.GENERAL_CHAT: "O módulo de conversa geral ainda não está disponível.",
}


class ResponseBuilder:
    """Construct the uniform public response without executing business logic."""

    def ensure_conversation_id(self, conversation_id: str | None) -> str:
        """Preserve a supplied conversation ID or generate a new UUID."""

        return conversation_id or str(uuid4())

    def from_module(
        self,
        conversation_id: str,
        result: ModuleResult,
    ) -> ChatResponse:
        """Convert a module result into a public assistant response."""

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=str(uuid4()),
            answer=result.answer,
            intent=result.intent,
            module=result.module,
            data=result.data,
            suggested_actions=result.suggested_actions,
        )

    def unavailable(
        self,
        conversation_id: str,
        intent: ChatIntent,
    ) -> ChatResponse:
        """Build a safe response for a recognized but unregistered module."""

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=str(uuid4()),
            answer=_UNAVAILABLE_MESSAGES.get(
                intent,
                "A funcionalidade solicitada ainda não está disponível.",
            ),
            intent=intent,
            module="unavailable",
        )

    def unknown(self, conversation_id: str) -> ChatResponse:
        """Build the default response for an unrecognized request."""

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=str(uuid4()),
            answer=(
                "Não identifiquei uma funcionalidade disponível para esta solicitação."
            ),
            intent=ChatIntent.UNKNOWN,
            module="unavailable",
        )
