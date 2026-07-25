"""Shared validation and normalization for uploaded food images."""

import base64
import io
import warnings
from dataclasses import dataclass

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import (
    ApplicationError,
    EmptyImageError,
    ImageProcessingError,
    ImageTooLargeError,
    InvalidImageError,
    UnsupportedImageFormatError,
)


@dataclass(frozen=True)
class PreparedImage:
    """Normalized image payload and safe processing metadata."""

    data_url: str
    width: int
    height: int
    original_size_bytes: int


class ImagePreprocessor:
    """Validate uploads and convert supported images into bounded JPEG data URLs."""

    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
    ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}

    def __init__(
        self,
        max_size_mb: int = 10,
        max_dimension: int = 1600,
    ) -> None:
        """Configure byte and pixel limits for normalized uploads."""

        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_dimension = max_dimension

    async def prepare(self, upload: UploadFile) -> PreparedImage:
        """
        Validate and prepare an uploaded image without blocking the event loop.

        Pillow processing runs in a threadpool because decoding and encoding
        are synchronous CPU-bound operations.
        """

        if upload.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise UnsupportedImageFormatError("Utilize uma imagem JPEG, PNG ou WebP.")

        # Reading one byte beyond the limit detects oversized uploads without
        # loading an arbitrarily large request into process memory.
        content = await upload.read(self.max_size_bytes + 1)

        if not content:
            raise EmptyImageError()

        if len(content) > self.max_size_bytes:
            raise ImageTooLargeError(
                f"A imagem deve ter no máximo "
                f"{self.max_size_bytes // (1024 * 1024)} MB."
            )

        try:
            # Pillow decoding and JPEG encoding are synchronous, so move them
            # off the event loop used by concurrent FastAPI requests.
            return await run_in_threadpool(self._process_content, content)
        except ApplicationError:
            raise
        except (
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
            UnidentifiedImageError,
            OSError,
            SyntaxError,
        ) as exc:
            raise InvalidImageError(
                "O conteúdo enviado não representa uma imagem válida."
            ) from exc
        except Exception as exc:
            raise ImageProcessingError() from exc

    def _process_content(self, content: bytes) -> PreparedImage:
        """Verify bytes, normalize pixels, and encode the prepared Data URL."""

        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)

            with Image.open(io.BytesIO(content)) as source:
                detected_format = source.format
                if detected_format not in self.ALLOWED_IMAGE_FORMATS:
                    raise UnsupportedImageFormatError()
                source.verify()

            # verify() checks integrity but leaves the decoder unusable for
            # transformations, requiring a fresh Image instance.
            with Image.open(io.BytesIO(content)) as source:
                # Normalize orientation and color mode before resizing so every
                # downstream analyzer receives a predictable pixel layout.
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail(
                    (self.max_dimension, self.max_dimension),
                    Image.Resampling.LANCZOS,
                )

                with io.BytesIO() as output:
                    # A single JPEG representation gives the OpenAI adapter one
                    # stable MIME type regardless of the original input format.
                    image.save(
                        output,
                        format="JPEG",
                        quality=85,
                        optimize=True,
                    )
                    encoded_image = base64.b64encode(output.getvalue()).decode("ascii")

                return PreparedImage(
                    data_url=f"data:image/jpeg;base64,{encoded_image}",
                    width=image.width,
                    height=image.height,
                    original_size_bytes=len(content),
                )
