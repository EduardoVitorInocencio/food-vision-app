"""Deterministic chat intent routing."""

from app.chat.schemas import ChatIntent

_INTENT_TERMS: tuple[tuple[ChatIntent, tuple[str, ...]], ...] = (
    (
        ChatIntent.ALLERGEN_ANALYSIS,
        ("alergeno", "alergia", "alergico", "allergen", "allergy"),
    ),
    (
        ChatIntent.MEAL_COMPARISON,
        ("compare", "comparar", "comparacao", "refeicao anterior", "previous meal"),
    ),
    (
        ChatIntent.KNOWLEDGE_RAG,
        ("base rag", "knowledge base", "base de conhecimento", "documentos"),
    ),
    (
        ChatIntent.FOOD_IDENTIFICATION,
        ("identifique o alimento", "qual e este alimento", "what food is this"),
    ),
)


class IntentRouter:
    async def detect(
        self,
        message: str | None,
        has_image: bool,
        available_modules: set[ChatIntent],
    ) -> ChatIntent:
        normalized = _normalize(message)

        for intent, terms in _INTENT_TERMS:
            if any(term in normalized for term in terms):
                return intent

        if has_image and ChatIntent.NUTRITION_ANALYSIS in available_modules:
            return ChatIntent.NUTRITION_ANALYSIS

        return ChatIntent.UNKNOWN


def _normalize(message: str | None) -> str:
    translation = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    return (message or "").strip().lower().translate(translation)
