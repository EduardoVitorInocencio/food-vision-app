"""Food analysis service."""

import logging
from typing import Protocol

from fastapi import UploadFile

from app.modules.nutrition_analysis.schemas import FoodAnalysis
from app.services.image_preprocessor import ImagePreprocessor, PreparedImage

logger = logging.getLogger(__name__)


class FoodAnalyzer(Protocol):
    async def analyze(self, image: PreparedImage) -> FoodAnalysis: ...


class FoodAnalysisService:
    def __init__(
        self,
        image_preprocessor: ImagePreprocessor,
        analyzer: FoodAnalyzer,
    ) -> None:
        self.image_preprocessor = image_preprocessor
        self.analyzer = analyzer

    async def analyze(self, upload: UploadFile) -> FoodAnalysis:
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
