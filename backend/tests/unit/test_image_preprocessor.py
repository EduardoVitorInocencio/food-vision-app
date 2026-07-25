"""Tests for image preprocessing."""

import base64
import io
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import UploadFile
from PIL import Image
from starlette.datastructures import Headers

from app.core.exceptions import (
    EmptyImageError,
    ImageTooLargeError,
    InvalidImageError,
    UnsupportedImageFormatError,
)
from app.services.image_preprocessor import ImagePreprocessor


def make_image(
    *,
    image_format: str = "PNG",
    size: tuple[int, int] = (120, 80),
    mode: str = "RGB",
) -> bytes:
    """Create image bytes with configurable format, size, and mode."""

    with io.BytesIO() as buffer:
        Image.new(mode, size, color="white").save(buffer, format=image_format)
        return buffer.getvalue()


def make_upload(content: bytes, content_type: str) -> UploadFile:
    """Wrap bytes in an UploadFile with a declared MIME type."""

    return UploadFile(
        file=io.BytesIO(content),
        filename="food-image",
        headers=Headers({"content-type": content_type}),
    )


@pytest.mark.asyncio
async def test_prepare_converts_valid_image_to_jpeg_data_url() -> None:
    """Normalize a valid image into a JPEG Data URL."""

    content = make_image(image_format="PNG")
    prepared = await ImagePreprocessor().prepare(make_upload(content, "image/png"))

    prefix, encoded = prepared.data_url.split(",", maxsplit=1)
    assert prefix == "data:image/jpeg;base64"
    assert base64.b64decode(encoded).startswith(b"\xff\xd8")
    assert (prepared.width, prepared.height) == (120, 80)
    assert prepared.original_size_bytes == len(content)


@pytest.mark.asyncio
async def test_prepare_rejects_empty_file() -> None:
    """Reject an upload with no bytes."""

    with pytest.raises(EmptyImageError):
        await ImagePreprocessor().prepare(make_upload(b"", "image/png"))


@pytest.mark.asyncio
async def test_prepare_rejects_unsupported_content_type() -> None:
    """Reject a declared MIME type outside the allowlist."""

    with pytest.raises(UnsupportedImageFormatError):
        await ImagePreprocessor().prepare(
            make_upload(make_image(), "application/octet-stream")
        )


@pytest.mark.asyncio
async def test_prepare_rejects_corrupted_image() -> None:
    """Reject bytes that Pillow cannot decode."""

    with pytest.raises(InvalidImageError):
        await ImagePreprocessor().prepare(make_upload(b"not-an-image", "image/png"))


@pytest.mark.asyncio
async def test_prepare_reads_only_up_to_configured_limit() -> None:
    """Read only one byte beyond the configured maximum."""

    preprocessor = ImagePreprocessor(max_size_mb=1)
    upload = Mock(content_type="image/png")
    upload.read = AsyncMock(return_value=b"x" * (1024 * 1024 + 1))

    with pytest.raises(ImageTooLargeError):
        await preprocessor.prepare(upload)

    upload.read.assert_awaited_once_with(1024 * 1024 + 1)


@pytest.mark.asyncio
async def test_prepare_rejects_disguised_unsupported_format() -> None:
    """Reject a GIF even when its declared MIME type is JPEG."""

    gif = make_image(image_format="GIF")

    with pytest.raises(UnsupportedImageFormatError):
        await ImagePreprocessor().prepare(make_upload(gif, "image/jpeg"))


@pytest.mark.asyncio
async def test_prepare_resizes_while_preserving_aspect_ratio() -> None:
    """Resize oversized pixels without distorting aspect ratio."""

    prepared = await ImagePreprocessor(max_dimension=100).prepare(
        make_upload(make_image(size=(400, 200)), "image/png")
    )

    assert (prepared.width, prepared.height) == (100, 50)
