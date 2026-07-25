"""Deterministic chat intent routing."""

from app.chat.schemas import ChatIntent

_INTENT_TERMS: tuple[tuple[ChatIntent, tuple[str, ...]], ...] = (
    # Keep specific, unavailable capabilities before the image fallback so a
    # request such as "analyze allergens in this image" is not misrouted to
    # nutrition merely because an upload is present.
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
    """Classify chat input with deterministic, testable rules."""

    async def detect(
        self,
        message: str | None,
        has_image: bool,
        available_modules: set[ChatIntent],
    ) -> ChatIntent:
        """
        Detect intent without an additional model call.

        Specific keyword rules take precedence over the image fallback, and
        only a registered nutrition module can receive that fallback.
        """

        normalized = _normalize(message)

        # Terms are stored without accents because _normalize applies the same
        # transformation to user input before this ordered comparison.
        for intent, terms in _INTENT_TERMS:
            if any(term in normalized for term in terms):
                return intent

        # Image-only interactions are the sole generic fallback currently
        # supported, and only when nutrition is actually registered.
        if has_image and ChatIntent.NUTRITION_ANALYSIS in available_modules:
            return ChatIntent.NUTRITION_ANALYSIS

        return ChatIntent.UNKNOWN


def _normalize(message: str | None) -> str:
    """Lowercase, trim, and remove accents before keyword matching."""

    translation = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    return (message or "").strip().lower().translate(translation)
