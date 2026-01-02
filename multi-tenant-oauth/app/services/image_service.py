"""Image upload and storage service."""

import os
import uuid
from pathlib import Path
from typing import Optional
import shutil
from fastapi import UploadFile

# Optional S3 support
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class ImageService:
    """Service for handling image uploads and storage."""

    def __init__(self):
        """Initialize image service."""
        self.use_s3 = os.getenv("USE_S3_STORAGE", "false").lower() == "true" and HAS_BOTO3
        self.local_upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads/images"))
        self.local_upload_dir.mkdir(parents=True, exist_ok=True)

        if self.use_s3:
            if not HAS_BOTO3:
                print("Warning: boto3 not installed. S3 storage disabled. Using local storage.")
                self.use_s3 = False
            else:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                    region_name=os.getenv("AWS_REGION", "us-east-1"),
                )
                self.bucket_name = os.getenv("S3_BUCKET_NAME")

    async def upload_image(
        self,
        file: UploadFile,
        tenant_id: str,
    ) -> tuple[str, str]:
        """
        Upload an image file.

        Args:
            file: Uploaded file
            tenant_id: Tenant UUID

        Returns:
            Tuple of (file_path, public_url)
        """
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise ValueError(f"Invalid file type: {file.content_type}")

        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Create tenant-specific directory
        relative_path = f"{tenant_id}/{unique_filename}"

        if self.use_s3:
            # Upload to S3
            file_url = await self._upload_to_s3(file, relative_path)
            return relative_path, file_url
        else:
            # Save locally
            file_path = self.local_upload_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save file
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Generate URL
            base_url = os.getenv("API_URL", "http://localhost:8000")
            file_url = f"{base_url}/uploads/images/{relative_path}"

            return str(relative_path), file_url

    async def save_image_bytes(
        self,
        image_bytes: bytes,
        filename: str,
        tenant_id: str,
    ) -> tuple[str, str]:
        """
        Save image from bytes.

        Args:
            image_bytes: Image data as bytes
            filename: Filename to use
            tenant_id: Tenant UUID

        Returns:
            Tuple of (file_path, public_url)
        """
        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Create tenant-specific directory
        relative_path = f"{tenant_id}/{unique_filename}"

        if self.use_s3:
            # Upload to S3
            from io import BytesIO
            file_url = await self._upload_bytes_to_s3(image_bytes, relative_path, f"image/{file_extension.lstrip('.')}")
            return relative_path, file_url
        else:
            # Save locally
            file_path = self.local_upload_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write bytes to file
            with file_path.open("wb") as f:
                f.write(image_bytes)

            # Generate URL
            base_url = os.getenv("API_URL", "http://localhost:8000")
            file_url = f"{base_url}/uploads/images/{relative_path}"

            return str(relative_path), file_url

    async def _upload_bytes_to_s3(self, image_bytes: bytes, key: str, content_type: str) -> str:
        """Upload bytes to S3."""
        try:
            from io import BytesIO

            # Upload to S3
            self.s3_client.upload_fileobj(
                BytesIO(image_bytes),
                self.bucket_name,
                key,
                ExtraArgs={
                    "ContentType": content_type,
                    "ACL": "public-read",
                },
            )

            # Generate public URL
            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
            return file_url

        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    async def _upload_to_s3(self, file: UploadFile, key: str) -> str:
        """Upload file to S3."""
        try:
            # Reset file pointer
            await file.seek(0)

            # Upload to S3
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                key,
                ExtraArgs={
                    "ContentType": file.content_type,
                    "ACL": "public-read",
                },
            )

            # Generate public URL
            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
            return file_url

        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    def delete_image(self, file_path: str) -> bool:
        """
        Delete an image.

        Args:
            file_path: Relative file path

        Returns:
            True if successful
        """
        if self.use_s3:
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                )
                return True
            except ClientError:
                return False
        else:
            full_path = self.local_upload_dir / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False

    def get_image_url(self, file_path: str) -> str:
        """
        Get public URL for an image.

        Args:
            file_path: Relative file path

        Returns:
            Public URL
        """
        if self.use_s3:
            return f"https://{self.bucket_name}.s3.amazonaws.com/{file_path}"
        else:
            base_url = os.getenv("API_URL", "http://localhost:8000")
            return f"{base_url}/uploads/images/{file_path}"
