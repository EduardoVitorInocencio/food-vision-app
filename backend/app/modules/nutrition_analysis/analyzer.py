"""OpenAI food analyzer integration."""

import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    OpenAIError,
    RateLimitError,
)
from openai.types.responses import ResponseInputParam

from app.core.exceptions import (
    InvalidOpenAIResponseError,
    OpenAIServiceError,
    OpenAIUnavailableError,
)
from app.modules.nutrition_analysis.prompts import FOOD_ANALYSIS_SYSTEM_PROMPT
from app.modules.nutrition_analysis.schemas import FoodAnalysis
from app.services.image_preprocessor import PreparedImage

logger = logging.getLogger(__name__)


class OpenAIFoodAnalyzer:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client = client
        self.model = model

    async def analyze(self, image: PreparedImage) -> FoodAnalysis:
        request_input: ResponseInputParam = [
            {
                "role": "system",
                "content": FOOD_ANALYSIS_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Analise esta imagem de alimento.",
                    },
                    {
                        "type": "input_image",
                        "image_url": image.data_url,
                        "detail": "auto",
                    },
                ],
            },
        ]

        try:
            response = await self.client.responses.parse(
                model=self.model,
                input=request_input,
                text_format=FoodAnalysis,
            )
        except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
            logger.error(
                "Falha temporária na comunicação com a OpenAI: %s",
                type(exc).__name__,
                exc_info=True,
            )
            raise OpenAIUnavailableError() from exc
        except APIStatusError as exc:
            logger.error(
                "OpenAI retornou status HTTP %s",
                exc.status_code,
                exc_info=True,
            )
            raise OpenAIServiceError() from exc
        except OpenAIError as exc:
            logger.error(
                "Falha no SDK da OpenAI: %s",
                type(exc).__name__,
                exc_info=True,
            )
            raise OpenAIServiceError() from exc

        if response.output_parsed is None:
            logger.warning(
                "OpenAI não retornou saída estruturada (response_id=%s)",
                response.id,
            )
            raise InvalidOpenAIResponseError()

        return response.output_parsed
