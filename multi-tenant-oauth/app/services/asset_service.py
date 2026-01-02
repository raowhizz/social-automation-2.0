"""Asset service for managing brand assets."""

from typing import List, Optional, Dict
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from fastapi import UploadFile
from PIL import Image
import io

from app.models import BrandAsset, AssetFolder
from app.services.image_service import ImageService
from app.utils.image_downloader import ImageDownloader


class AssetService:
    """Service for managing brand assets."""

    def __init__(self):
        """Initialize asset service."""
        self.image_service = ImageService()
        self.image_downloader = ImageDownloader()

    async def upload_asset(
        self,
        db: Session,
        file: UploadFile,
        tenant_id: str,
        folder_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> BrandAsset:
        """
        Upload a new brand asset.

        Args:
            db: Database session
            file: Uploaded file
            tenant_id: Tenant UUID
            folder_id: Optional folder UUID
            title: Optional title
            description: Optional description
            tags: Optional list of tags

        Returns:
            Created brand asset
        """
        # Upload file using ImageService
        file_path, file_url = await self.image_service.upload_image(file, tenant_id)

        # Get image dimensions
        width, height = await self._get_image_dimensions(file)

        # Create brand asset record
        asset = BrandAsset(
            tenant_id=uuid.UUID(tenant_id),
            folder_id=uuid.UUID(folder_id) if folder_id else None,
            filename=file.filename,
            file_path=file_path,
            file_url=file_url,
            file_size=file.size if hasattr(file, 'size') else None,
            mime_type=file.content_type,
            width=width,
            height=height,
            title=title or file.filename,
            description=description,
            tags=tags or [],
        )

        db.add(asset)
        db.commit()
        db.refresh(asset)

        return asset

    async def create_asset_from_url(
        self,
        db: Session,
        url: str,
        tenant_id: str,
        folder_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[BrandAsset]:
        """
        Create a brand asset by downloading image from URL.

        Args:
            db: Database session
            url: Image URL to download
            tenant_id: Tenant UUID
            folder_id: Optional folder UUID
            title: Optional title
            description: Optional description
            tags: Optional list of tags

        Returns:
            Created brand asset or None if download failed
        """
        # Download image from URL
        download_result = await self.image_downloader.download_image(url)

        if download_result is None:
            # Download failed (timeout, invalid image, etc.)
            return None

        image_bytes, content_type, width, height = download_result

        # Get file extension from content type
        file_extension = self.image_downloader.get_file_extension(content_type)

        # Generate filename from URL or use UUID
        import os
        url_filename = os.path.basename(url.split('?')[0])  # Remove query params
        if url_filename and '.' in url_filename:
            filename = url_filename
        else:
            filename = f"menu_item_{uuid.uuid4()}{file_extension}"

        # Save image using ImageService
        try:
            file_path, file_url = await self.image_service.save_image_bytes(
                image_bytes=image_bytes,
                filename=filename,
                tenant_id=tenant_id
            )
        except Exception as e:
            print(f"Error saving downloaded image: {e}")
            return None

        # Create brand asset record
        asset = BrandAsset(
            tenant_id=uuid.UUID(tenant_id),
            folder_id=uuid.UUID(folder_id) if folder_id else None,
            filename=filename,
            file_path=file_path,
            file_url=file_url,
            file_size=len(image_bytes),
            mime_type=content_type,
            width=width,
            height=height,
            title=title or filename,
            description=description,
            tags=tags or [],
        )

        db.add(asset)
        db.commit()
        db.refresh(asset)

        return asset

    async def _get_image_dimensions(self, file: UploadFile) -> tuple[Optional[int], Optional[int]]:
        """
        Get image dimensions from uploaded file.

        Args:
            file: Uploaded file

        Returns:
            Tuple of (width, height) or (None, None)
        """
        try:
            # Read file contents
            await file.seek(0)
            contents = await file.read()
            await file.seek(0)  # Reset for future reads

            # Open image with PIL
            image = Image.open(io.BytesIO(contents))
            return image.width, image.height
        except Exception as e:
            print(f"Error getting image dimensions: {e}")
            return None, None

    def get_asset(self, db: Session, asset_id: str) -> Optional[BrandAsset]:
        """
        Get asset by ID.

        Args:
            db: Database session
            asset_id: Asset UUID

        Returns:
            Asset or None
        """
        return db.query(BrandAsset).filter(BrandAsset.id == uuid.UUID(asset_id)).first()

    def list_assets(
        self,
        db: Session,
        tenant_id: str,
        folder_id: Optional[str] = None,
        search_query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BrandAsset]:
        """
        List assets for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            folder_id: Optional folder UUID filter
            search_query: Optional search query (searches title, description, filename)
            tags: Optional list of tags to filter by
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of assets
        """
        query = db.query(BrandAsset).filter(BrandAsset.tenant_id == uuid.UUID(tenant_id))

        # Filter by folder
        if folder_id is not None:
            query = query.filter(BrandAsset.folder_id == uuid.UUID(folder_id))

        # Search filter
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    BrandAsset.title.ilike(search_pattern),
                    BrandAsset.description.ilike(search_pattern),
                    BrandAsset.filename.ilike(search_pattern),
                )
            )

        # Tags filter (JSONB containment)
        if tags:
            for tag in tags:
                query = query.filter(BrandAsset.tags.contains([tag]))

        # Order by most recent first
        query = query.order_by(desc(BrandAsset.created_at))

        # Pagination
        query = query.limit(limit).offset(offset)

        return query.all()

    def update_asset(
        self,
        db: Session,
        asset_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        folder_id: Optional[str] = None,
    ) -> Optional[BrandAsset]:
        """
        Update asset metadata.

        Args:
            db: Database session
            asset_id: Asset UUID
            title: Optional new title
            description: Optional new description
            tags: Optional new tags list
            folder_id: Optional new folder UUID

        Returns:
            Updated asset or None
        """
        asset = self.get_asset(db, asset_id)
        if not asset:
            return None

        if title is not None:
            asset.title = title
        if description is not None:
            asset.description = description
        if tags is not None:
            asset.tags = tags
        if folder_id is not None:
            asset.folder_id = uuid.UUID(folder_id) if folder_id else None

        db.commit()
        db.refresh(asset)

        return asset

    def move_asset(
        self, db: Session, asset_id: str, target_folder_id: Optional[str]
    ) -> Optional[BrandAsset]:
        """
        Move asset to a different folder.

        Args:
            db: Database session
            asset_id: Asset UUID
            target_folder_id: Target folder UUID (None for root)

        Returns:
            Updated asset or None
        """
        return self.update_asset(db, asset_id, folder_id=target_folder_id)

    def delete_asset(self, db: Session, asset_id: str) -> bool:
        """
        Delete an asset.

        Note: Also deletes the actual file from storage.

        Args:
            db: Database session
            asset_id: Asset UUID

        Returns:
            True if deleted, False if not found
        """
        asset = self.get_asset(db, asset_id)
        if not asset:
            return False

        # Delete file from storage
        try:
            self.image_service.delete_image(asset.file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

        # Delete database record
        db.delete(asset)
        db.commit()

        return True

    def search_assets(
        self,
        db: Session,
        tenant_id: str,
        query: str,
        limit: int = 50,
    ) -> List[BrandAsset]:
        """
        Search assets by title, description, or tags.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            query: Search query
            limit: Maximum results

        Returns:
            List of matching assets
        """
        return self.list_assets(
            db=db,
            tenant_id=tenant_id,
            search_query=query,
            limit=limit,
        )

    def mark_asset_used(self, db: Session, asset_id: str) -> Optional[BrandAsset]:
        """
        Mark an asset as used (increment usage count and update last used date).

        Args:
            db: Database session
            asset_id: Asset UUID

        Returns:
            Updated asset or None
        """
        asset = self.get_asset(db, asset_id)
        if not asset:
            return None

        asset.times_used += 1
        asset.last_used_at = datetime.utcnow()

        db.commit()
        db.refresh(asset)

        return asset

    def get_recently_used(
        self, db: Session, tenant_id: str, limit: int = 10
    ) -> List[BrandAsset]:
        """
        Get recently used assets.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            limit: Maximum results

        Returns:
            List of recently used assets
        """
        return (
            db.query(BrandAsset)
            .filter(
                and_(
                    BrandAsset.tenant_id == uuid.UUID(tenant_id),
                    BrandAsset.last_used_at != None,
                )
            )
            .order_by(desc(BrandAsset.last_used_at))
            .limit(limit)
            .all()
        )

    def get_assets_by_folder(
        self, db: Session, tenant_id: str, folder_name: str
    ) -> List[BrandAsset]:
        """
        Get all assets in a folder by folder name.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            folder_name: Folder name (e.g., "Dishes", "Brand Assets")

        Returns:
            List of assets
        """
        # Get folder by name
        folder = (
            db.query(AssetFolder)
            .filter(
                and_(
                    AssetFolder.tenant_id == uuid.UUID(tenant_id),
                    AssetFolder.name == folder_name,
                )
            )
            .first()
        )

        if not folder:
            return []

        return self.list_assets(db=db, tenant_id=tenant_id, folder_id=str(folder.id))
