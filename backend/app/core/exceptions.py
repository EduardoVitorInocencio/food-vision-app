"""Application exceptions."""

from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse


class ApplicationError(Exception):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = "application_error"
    default_message = "Ocorreu um erro ao processar a solicitação."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ImageError(ApplicationError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "invalid_image"


class EmptyImageError(ImageError):
    error_code = "empty_image"
    default_message = "A imagem enviada está vazia."


class UnsupportedImageFormatError(ImageError):
    status_code = HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    error_code = "unsupported_image_format"
    default_message = "Utilize uma imagem JPEG, PNG ou WebP."


class ImageTooLargeError(ImageError):
    status_code = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    error_code = "image_too_large"
    default_message = "A imagem excede o tamanho máximo permitido."


class InvalidImageError(ImageError):
    error_code = "invalid_image"
    default_message = "O conteúdo enviado não representa uma imagem válida."


class ImageProcessingError(ImageError):
    error_code = "image_processing_error"
    default_message = "Não foi possível processar a imagem enviada."


class OpenAIServiceError(ApplicationError):
    status_code = HTTPStatus.BAD_GATEWAY
    error_code = "openai_service_error"
    default_message = "Não foi possível analisar a imagem no momento."


class OpenAIUnavailableError(OpenAIServiceError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "openai_unavailable"


class InvalidOpenAIResponseError(OpenAIServiceError):
    error_code = "invalid_openai_response"
    default_message = "O serviço retornou uma análise inválida."


class ConfigurationError(ApplicationError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "service_not_configured"
    default_message = "O serviço de análise não está configurado."


async def application_error_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, ApplicationError):
        raise exc

    return JSONResponse(
        status_code=int(exc.status_code),
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            }
        },
    )
