"""Image downloader utility for downloading images from URLs."""

import httpx
import logging
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class ImageDownloader:
    """Download and validate images from URLs."""

    def __init__(self, timeout: int = 30):
        """
        Initialize image downloader.

        Args:
            timeout: Timeout in seconds for HTTP requests
        """
        self.timeout = timeout

    async def download_image(self, url: str) -> Optional[Tuple[bytes, str, int, int]]:
        """
        Download image from URL and validate it.

        Args:
            url: Image URL to download

        Returns:
            Tuple of (image_bytes, content_type, width, height) or None if failed

        Note:
            Silently returns None on any failure (network, timeout, validation, etc.)
        """
        try:
            # Download image with timeout
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Get image bytes
                image_bytes = response.content

                # Validate with PIL and get dimensions
                # We validate the actual image data instead of trusting content-type headers
                # (S3 buckets often return application/octet-stream instead of image/*)
                try:
                    image = Image.open(BytesIO(image_bytes))
                    width, height = image.size

                    # Verify image format is valid
                    if image.format not in ["JPEG", "PNG", "GIF", "WEBP", "BMP"]:
                        logger.warning(f"Unsupported image format: {image.format} for URL: {url}")
                        return None

                    # Generate proper content-type based on actual image format
                    format_to_mime = {
                        "JPEG": "image/jpeg",
                        "PNG": "image/png",
                        "GIF": "image/gif",
                        "WEBP": "image/webp",
                        "BMP": "image/bmp",
                    }
                    content_type = format_to_mime.get(image.format, "image/jpeg")

                    return (image_bytes, content_type, width, height)

                except Exception as e:
                    logger.warning(f"Failed to validate image from {url}: {str(e)}")
                    return None

        except httpx.TimeoutException:
            logger.warning(f"Timeout downloading image from {url}")
            return None

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error downloading image from {url}: {e.response.status_code}")
            return None

        except Exception as e:
            logger.warning(f"Failed to download image from {url}: {str(e)}")
            return None

    def get_file_extension(self, content_type: str) -> str:
        """
        Get file extension from content type.

        Args:
            content_type: HTTP content-type header value

        Returns:
            File extension (e.g., ".jpg", ".png")
        """
        content_type_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
        }

        # Clean content type (remove charset, etc.)
        clean_type = content_type.split(";")[0].strip().lower()

        return content_type_map.get(clean_type, ".jpg")  # Default to .jpg
