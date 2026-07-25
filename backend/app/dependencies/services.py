"""Service dependencies."""

from functools import lru_cache

from openai import AsyncOpenAI

from app.chat.context_manager import ContextManager
from app.chat.intent_router import IntentRouter
from app.chat.response_builder import ResponseBuilder
from app.chat.schemas import ChatIntent
from app.chat.service import ChatService
from app.core.config import get_settings
from app.integrations.openai.client import create_openai_client
from app.modules.nutrition_analysis.analyzer import OpenAIFoodAnalyzer
from app.modules.nutrition_analysis.service import (
    FoodAnalysisService,
    NutritionAnalysisModule,
)
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


@lru_cache
def get_nutrition_analysis_module() -> NutritionAnalysisModule:
    """Build the chat adapter around the existing nutrition service."""

    return NutritionAnalysisModule(get_food_analysis_service())


@lru_cache
def get_context_manager() -> ContextManager:
    """Provide the process-local conversation context store."""

    return ContextManager()


@lru_cache
def get_intent_router() -> IntentRouter:
    """Provide the deterministic chat intent router."""

    return IntentRouter()


@lru_cache
def get_response_builder() -> ResponseBuilder:
    """Provide the stateless chat response builder."""

    return ResponseBuilder()


@lru_cache
def get_chat_service() -> ChatService:
    """Compose chat orchestration with only implemented modules registered."""

    return ChatService(
        intent_router=get_intent_router(),
        context_manager=get_context_manager(),
        response_builder=get_response_builder(),
        modules={
            ChatIntent.NUTRITION_ANALYSIS: get_nutrition_analysis_module(),
        },
    )


async def close_services() -> None:
    """Release shared resources and clear dependency caches at shutdown."""

    if get_context_manager.cache_info().currsize:
        await get_context_manager().clear_all()

    if get_openai_client.cache_info().currsize:
        await get_openai_client().close()

    get_chat_service.cache_clear()
    get_response_builder.cache_clear()
    get_intent_router.cache_clear()
    get_context_manager.cache_clear()
    get_nutrition_analysis_module.cache_clear()
    get_food_analysis_service.cache_clear()
    get_food_analyzer.cache_clear()
    get_image_preprocessor.cache_clear()
    get_openai_client.cache_clear()
