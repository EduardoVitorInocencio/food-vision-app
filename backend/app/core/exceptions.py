"""Application exceptions."""

from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse


class ApplicationError(Exception):
    """Base error carrying a safe HTTP status, code, and public message."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = "application_error"
    default_message = "Ocorreu um erro ao processar a solicitação."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ImageError(ApplicationError):
    """Base error for upload validation and image processing failures."""

    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "invalid_image"


class EmptyImageError(ImageError):
    """Raised when an uploaded image has no content."""

    error_code = "empty_image"
    default_message = "A imagem enviada está vazia."


class UnsupportedImageFormatError(ImageError):
    """Raised when MIME type or decoded format is unsupported."""

    status_code = HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    error_code = "unsupported_image_format"
    default_message = "Utilize uma imagem JPEG, PNG ou WebP."


class ImageTooLargeError(ImageError):
    """Raised when an upload exceeds the configured byte limit."""

    status_code = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    error_code = "image_too_large"
    default_message = "A imagem excede o tamanho máximo permitido."


class InvalidImageError(ImageError):
    """Raised when uploaded bytes cannot be decoded as a safe image."""

    error_code = "invalid_image"
    default_message = "O conteúdo enviado não representa uma imagem válida."


class ImageProcessingError(ImageError):
    """Raised for unexpected failures while normalizing an image."""

    error_code = "image_processing_error"
    default_message = "Não foi possível processar a imagem enviada."


class OpenAIServiceError(ApplicationError):
    """Base error for failures returned by the OpenAI integration."""

    status_code = HTTPStatus.BAD_GATEWAY
    error_code = "openai_service_error"
    default_message = "Não foi possível analisar a imagem no momento."


class OpenAIUnavailableError(OpenAIServiceError):
    """Raised for transient connection, timeout, or rate-limit failures."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "openai_unavailable"


class InvalidOpenAIResponseError(OpenAIServiceError):
    """Raised when Structured Outputs does not contain parsed data."""

    error_code = "invalid_openai_response"
    default_message = "O serviço retornou uma análise inválida."


class ConfigurationError(ApplicationError):
    """Raised when a required service setting is absent."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "service_not_configured"
    default_message = "O serviço de análise não está configurado."


class EmptyChatMessageError(ApplicationError):
    """Raised when a chat request contains neither text nor image."""

    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "empty_chat_message"
    default_message = "Envie uma mensagem ou uma imagem."


async def application_error_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    """Translate known application errors into the stable public error envelope."""

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
