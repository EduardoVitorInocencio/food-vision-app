"""Service dependencies."""
from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.integrations.openai.food_analyzer import OpenAIFoodAnalyzer
from app.services.food_analysis_service import FoodAnalysisService
from app.services.image_preprocessor import ImagePreprocessor


@lru_cache
def get_openai_client() -> AsyncOpenAI:
    """
    Cria e reutiliza o cliente assíncrono da OpenAI.

    A chave da API e demais configurações são obtidas
    por meio das variáveis de ambiente da aplicação.
    """
    settings = get_settings()

    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )


@lru_cache
def get_image_preprocessor() -> ImagePreprocessor:
    """
    Cria o serviço responsável por validar, redimensionar
    e converter a imagem para o formato aceito pela OpenAI.
    """
    settings = get_settings()

    return ImagePreprocessor(
        max_size_mb=settings.max_image_size_mb,
        max_dimension=settings.max_image_dimension,
    )


@lru_cache
def get_food_analyzer() -> OpenAIFoodAnalyzer:
    """
    Cria o adaptador responsável pela comunicação com a OpenAI.
    """
    settings = get_settings()

    return OpenAIFoodAnalyzer(
        client=get_openai_client(),
        model=settings.openai_vision_model,
    )


@lru_cache
def get_food_analysis_service() -> FoodAnalysisService:
    """
    Monta o serviço principal da aplicação com todas
    as dependências necessárias.
    """
    return FoodAnalysisService(
        image_preprocessor=get_image_preprocessor(),
        analyzer=get_food_analyzer(),
    )