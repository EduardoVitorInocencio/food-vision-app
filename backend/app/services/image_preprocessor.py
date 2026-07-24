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
    data_url: str
    width: int
    height: int
    original_size_bytes: int


class ImagePreprocessor:
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
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_dimension = max_dimension

    async def prepare(self, upload: UploadFile) -> PreparedImage:
        if upload.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise UnsupportedImageFormatError("Utilize uma imagem JPEG, PNG ou WebP.")

        content = await upload.read(self.max_size_bytes + 1)

        if not content:
            raise EmptyImageError()

        if len(content) > self.max_size_bytes:
            raise ImageTooLargeError(
                f"A imagem deve ter no máximo "
                f"{self.max_size_bytes // (1024 * 1024)} MB."
            )

        try:
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
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)

            with Image.open(io.BytesIO(content)) as source:
                detected_format = source.format
                if detected_format not in self.ALLOWED_IMAGE_FORMATS:
                    raise UnsupportedImageFormatError()
                source.verify()

            with Image.open(io.BytesIO(content)) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail(
                    (self.max_dimension, self.max_dimension),
                    Image.Resampling.LANCZOS,
                )

                with io.BytesIO() as output:
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
