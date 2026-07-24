"""Service dependencies."""

from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.integrations.openai.client import create_openai_client
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

    return create_openai_client(settings)


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


async def close_services() -> None:
    if get_openai_client.cache_info().currsize:
        await get_openai_client().close()

    get_food_analysis_service.cache_clear()
    get_food_analyzer.cache_clear()
    get_image_preprocessor.cache_clear()
    get_openai_client.cache_clear()
