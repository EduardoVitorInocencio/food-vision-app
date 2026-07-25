"""Food analysis service."""

import logging
from typing import Protocol

from fastapi import UploadFile

from app.chat.schemas import ChatContext, ChatIntent, ModuleResult
from app.core.exceptions import EmptyChatMessageError
from app.modules.nutrition_analysis.schemas import FoodAnalysis
from app.services.image_preprocessor import ImagePreprocessor, PreparedImage

logger = logging.getLogger(__name__)


class FoodAnalyzer(Protocol):
    """Contract for analyzers that produce a validated food analysis."""

    async def analyze(self, image: PreparedImage) -> FoodAnalysis: ...


class FoodAnalysisService:
    """Coordinate shared image preparation and nutritional analysis."""

    def __init__(
        self,
        image_preprocessor: ImagePreprocessor,
        analyzer: FoodAnalyzer,
    ) -> None:
        self.image_preprocessor = image_preprocessor
        self.analyzer = analyzer

    async def analyze(self, upload: UploadFile) -> FoodAnalysis:
        """Prepare an upload and return its structured nutrition analysis."""

        logger.info("Iniciando análise de imagem")
        prepared = await self.image_preprocessor.prepare(upload)
        analysis = await self.analyzer.analyze(prepared)
        logger.info(
            "Análise concluída para imagem %sx%s (%s bytes)",
            prepared.width,
            prepared.height,
            prepared.original_size_bytes,
        )
        return analysis


class NutritionAnalysisModule:
    """Adapt the existing nutrition service to the common chat contract."""

    def __init__(self, service: FoodAnalysisService) -> None:
        self.service = service

    async def execute(
        self,
        *,
        message: str | None,
        image: UploadFile | None,
        context: ChatContext,
    ) -> ModuleResult:
        """Execute image analysis and expose its result as a chat module."""

        del message, context
        if image is None:
            raise EmptyChatMessageError("Envie uma imagem para análise nutricional.")

        analysis = await self.service.analyze(image)
        data = analysis.model_dump(mode="json")
        return ModuleResult(
            answer=_build_nutrition_answer(analysis),
            intent=ChatIntent.NUTRITION_ANALYSIS,
            module=ChatIntent.NUTRITION_ANALYSIS.value,
            data=data,
            context_updates={"last_nutrition_analysis": data},
        )


def _build_nutrition_answer(analysis: FoodAnalysis) -> str:
    """Derive conversational text from validated data without another API call."""

    calories = analysis.total_nutrition.calories
    if calories is not None:
        return (
            f"{analysis.dish_name}: estimativa total de {calories:g} kcal. "
            "Consulte os dados estruturados para os demais nutrientes."
        )

    lower = analysis.total_calorie_range.min
    upper = analysis.total_calorie_range.max
    if lower is not None and upper is not None:
        return (
            f"{analysis.dish_name}: estimativa entre {lower:g} e {upper:g} kcal. "
            "Consulte os dados estruturados para os demais nutrientes."
        )

    return (
        f"{analysis.dish_name}: análise nutricional concluída. "
        "Consulte os dados estruturados para os detalhes."
    )
