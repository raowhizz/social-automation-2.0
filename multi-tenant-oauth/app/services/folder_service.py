"""Folder service for managing asset folders."""

from typing import List, Optional, Dict
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import AssetFolder, Tenant


class FolderService:
    """Service for managing asset folders."""

    DEFAULT_FOLDERS = [
        {"name": "Brand Assets", "description": "Logos, branding materials", "display_order": 1},
        {"name": "Dishes", "description": "Food and menu item photos", "display_order": 2},
        {"name": "Exterior", "description": "Restaurant exterior photos", "display_order": 3},
        {"name": "Interior", "description": "Restaurant interior photos", "display_order": 4},
        {"name": "Events", "description": "Special events and celebrations", "display_order": 5},
    ]

    def create_folder(
        self,
        db: Session,
        tenant_id: str,
        name: str,
        description: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        is_default: str = 'N',
    ) -> AssetFolder:
        """
        Create a new folder.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            name: Folder name
            description: Optional description
            parent_folder_id: Optional parent folder UUID
            is_default: 'Y' or 'N' to mark as default folder

        Returns:
            Created folder
        """
        folder = AssetFolder(
            tenant_id=uuid.UUID(tenant_id),
            name=name,
            description=description,
            parent_folder_id=uuid.UUID(parent_folder_id) if parent_folder_id else None,
            is_default=is_default,
            display_order=0,
        )

        db.add(folder)
        db.commit()
        db.refresh(folder)

        return folder

    def get_folder(self, db: Session, folder_id: str) -> Optional[AssetFolder]:
        """
        Get folder by ID.

        Args:
            db: Database session
            folder_id: Folder UUID

        Returns:
            Folder or None
        """
        return db.query(AssetFolder).filter(AssetFolder.id == uuid.UUID(folder_id)).first()

    def list_folders(
        self,
        db: Session,
        tenant_id: str,
        parent_folder_id: Optional[str] = None,
    ) -> List[AssetFolder]:
        """
        List folders for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            parent_folder_id: Optional parent folder UUID (None for root folders)

        Returns:
            List of folders
        """
        query = db.query(AssetFolder).filter(AssetFolder.tenant_id == uuid.UUID(tenant_id))

        if parent_folder_id is None:
            query = query.filter(AssetFolder.parent_folder_id == None)
        else:
            query = query.filter(AssetFolder.parent_folder_id == uuid.UUID(parent_folder_id))

        return query.order_by(AssetFolder.display_order, AssetFolder.name).all()

    def get_folder_tree(self, db: Session, tenant_id: str) -> List[Dict]:
        """
        Get complete folder tree for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID

        Returns:
            List of folder dictionaries with nested subfolders
        """
        # Get all folders for tenant
        all_folders = (
            db.query(AssetFolder)
            .filter(AssetFolder.tenant_id == uuid.UUID(tenant_id))
            .order_by(AssetFolder.display_order, AssetFolder.name)
            .all()
        )

        # Build folder map
        folder_map = {}
        root_folders = []

        for folder in all_folders:
            folder_dict = {
                "id": str(folder.id),
                "name": folder.name,
                "description": folder.description,
                "display_order": folder.display_order,
                "is_default": folder.is_default,
                "parent_folder_id": str(folder.parent_folder_id) if folder.parent_folder_id else None,
                "subfolders": [],
                "asset_count": len(folder.assets) if folder.assets else 0,
            }

            folder_map[str(folder.id)] = folder_dict

            if folder.parent_folder_id is None:
                root_folders.append(folder_dict)

        # Build tree structure
        for folder_dict in folder_map.values():
            if folder_dict["parent_folder_id"]:
                parent = folder_map.get(folder_dict["parent_folder_id"])
                if parent:
                    parent["subfolders"].append(folder_dict)

        return root_folders

    def update_folder(
        self,
        db: Session,
        folder_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        display_order: Optional[int] = None,
    ) -> Optional[AssetFolder]:
        """
        Update folder properties.

        Args:
            db: Database session
            folder_id: Folder UUID
            name: Optional new name
            description: Optional new description
            display_order: Optional new display order

        Returns:
            Updated folder or None
        """
        folder = self.get_folder(db, folder_id)
        if not folder:
            return None

        if name is not None:
            folder.name = name
        if description is not None:
            folder.description = description
        if display_order is not None:
            folder.display_order = display_order

        db.commit()
        db.refresh(folder)

        return folder

    def delete_folder(self, db: Session, folder_id: str) -> bool:
        """
        Delete a folder.

        Note: This will also delete all assets in the folder (CASCADE).

        Args:
            db: Database session
            folder_id: Folder UUID

        Returns:
            True if deleted, False if not found
        """
        folder = self.get_folder(db, folder_id)
        if not folder:
            return False

        # Don't allow deleting default folders
        if folder.is_default == 'Y':
            raise ValueError("Cannot delete default folders")

        db.delete(folder)
        db.commit()

        return True

    def create_default_folders(self, db: Session, tenant_id: str) -> List[AssetFolder]:
        """
        Create default folders for a new tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID

        Returns:
            List of created folders
        """
        created_folders = []

        for folder_data in self.DEFAULT_FOLDERS:
            folder = AssetFolder(
                tenant_id=uuid.UUID(tenant_id),
                name=folder_data["name"],
                description=folder_data["description"],
                display_order=folder_data["display_order"],
                is_default='Y',
            )
            db.add(folder)
            created_folders.append(folder)

        db.commit()

        return created_folders

    def get_folder_by_name(
        self, db: Session, tenant_id: str, name: str
    ) -> Optional[AssetFolder]:
        """
        Get folder by name.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            name: Folder name

        Returns:
            Folder or None
        """
        return (
            db.query(AssetFolder)
            .filter(
                and_(
                    AssetFolder.tenant_id == uuid.UUID(tenant_id),
                    AssetFolder.name == name,
                )
            )
            .first()
        )

    def get_or_create_category_folder(
        self, db: Session, tenant_id: str, category_name: str
    ) -> AssetFolder:
        """
        Get or create a category subfolder under the Dishes folder.

        Creates hierarchical structure: Dishes/CategoryName (e.g., Dishes/Pizza)

        Args:
            db: Database session
            tenant_id: Tenant UUID
            category_name: Category name (e.g., "Pizza", "Pasta", "Appetizers")

        Returns:
            Category folder
        """
        # Ensure "Dishes" parent folder exists
        dishes_folder = self.get_folder_by_name(db, tenant_id, "Dishes")

        if not dishes_folder:
            # Create Dishes folder if it doesn't exist
            dishes_folder = self.create_folder(
                db=db,
                tenant_id=tenant_id,
                name="Dishes",
                description="Food and menu item photos",
                is_default='Y',
            )

        # Check if category subfolder exists
        category_folder = (
            db.query(AssetFolder)
            .filter(
                and_(
                    AssetFolder.tenant_id == uuid.UUID(tenant_id),
                    AssetFolder.parent_folder_id == dishes_folder.id,
                    AssetFolder.name == category_name,
                )
            )
            .first()
        )

        if not category_folder:
            # Create category subfolder
            category_folder = self.create_folder(
                db=db,
                tenant_id=tenant_id,
                name=category_name,
                description=f"{category_name} dishes",
                parent_folder_id=str(dishes_folder.id),
                is_default='N',
            )

        return category_folder
