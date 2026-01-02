"""API endpoints for brand assets and folders."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.base import get_db
from app.services import AssetService, FolderService


router = APIRouter(prefix="/api/v1", tags=["assets"])

# Initialize services
asset_service = AssetService()
folder_service = FolderService()


# ==================== Request/Response Models ====================

class CreateFolderRequest(BaseModel):
    """Request model for creating a folder."""
    tenant_id: str
    name: str
    description: Optional[str] = None
    parent_folder_id: Optional[str] = None


class UpdateFolderRequest(BaseModel):
    """Request model for updating a folder."""
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None


class UpdateAssetRequest(BaseModel):
    """Request model for updating asset metadata."""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    folder_id: Optional[str] = None


class MoveAssetRequest(BaseModel):
    """Request model for moving an asset."""
    target_folder_id: Optional[str] = None


class AssetResponse(BaseModel):
    """Response model for asset."""
    id: str
    tenant_id: str
    folder_id: Optional[str]
    filename: str
    file_url: str
    file_size: Optional[int]
    mime_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    title: Optional[str]
    description: Optional[str]
    tags: List[str]
    times_used: int
    last_used_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class FolderResponse(BaseModel):
    """Response model for folder."""
    id: str
    tenant_id: str
    parent_folder_id: Optional[str]
    name: str
    description: Optional[str]
    display_order: int
    is_default: str
    created_at: str

    class Config:
        from_attributes = True


# ==================== Asset Endpoints ====================

@router.post("/assets/upload", response_model=AssetResponse)
async def upload_asset(
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    folder_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated string
    db: Session = Depends(get_db),
):
    """
    Upload a new brand asset.

    Args:
        file: Image file to upload
        tenant_id: Tenant UUID
        folder_id: Optional folder UUID
        title: Optional title
        description: Optional description
        tags: Optional comma-separated tags

    Returns:
        Created asset
    """
    try:
        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        # Upload asset
        asset = await asset_service.upload_asset(
            db=db,
            file=file,
            tenant_id=tenant_id,
            folder_id=folder_id,
            title=title,
            description=description,
            tags=tag_list,
        )

        return AssetResponse(
            id=str(asset.id),
            tenant_id=str(asset.tenant_id),
            folder_id=str(asset.folder_id) if asset.folder_id else None,
            filename=asset.filename,
            file_url=asset.file_url,
            file_size=asset.file_size,
            mime_type=asset.mime_type,
            width=asset.width,
            height=asset.height,
            title=asset.title,
            description=asset.description,
            tags=asset.tags or [],
            times_used=asset.times_used,
            last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
            created_at=asset.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload asset: {str(e)}")


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    tenant_id: str = Query(...),
    folder_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List assets for a tenant.

    Args:
        tenant_id: Tenant UUID
        folder_id: Optional folder UUID filter
        search: Optional search query
        tags: Optional comma-separated tags
        limit: Max results (default 100, max 500)
        offset: Pagination offset

    Returns:
        List of assets
    """
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    assets = asset_service.list_assets(
        db=db,
        tenant_id=tenant_id,
        folder_id=folder_id,
        search_query=search,
        tags=tag_list,
        limit=limit,
        offset=offset,
    )

    return [
        AssetResponse(
            id=str(asset.id),
            tenant_id=str(asset.tenant_id),
            folder_id=str(asset.folder_id) if asset.folder_id else None,
            filename=asset.filename,
            file_url=asset.file_url,
            file_size=asset.file_size,
            mime_type=asset.mime_type,
            width=asset.width,
            height=asset.height,
            title=asset.title,
            description=asset.description,
            tags=asset.tags or [],
            times_used=asset.times_used,
            last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
            created_at=asset.created_at.isoformat(),
        )
        for asset in assets
    ]


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a specific asset by ID.

    Args:
        asset_id: Asset UUID

    Returns:
        Asset details
    """
    asset = asset_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return AssetResponse(
        id=str(asset.id),
        tenant_id=str(asset.tenant_id),
        folder_id=str(asset.folder_id) if asset.folder_id else None,
        filename=asset.filename,
        file_url=asset.file_url,
        file_size=asset.file_size,
        mime_type=asset.mime_type,
        width=asset.width,
        height=asset.height,
        title=asset.title,
        description=asset.description,
        tags=asset.tags or [],
        times_used=asset.times_used,
        last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
        created_at=asset.created_at.isoformat(),
    )


@router.patch("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    request: UpdateAssetRequest,
    db: Session = Depends(get_db),
):
    """
    Update asset metadata.

    Args:
        asset_id: Asset UUID
        request: Update data

    Returns:
        Updated asset
    """
    asset = asset_service.update_asset(
        db=db,
        asset_id=asset_id,
        title=request.title,
        description=request.description,
        tags=request.tags,
        folder_id=request.folder_id,
    )

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return AssetResponse(
        id=str(asset.id),
        tenant_id=str(asset.tenant_id),
        folder_id=str(asset.folder_id) if asset.folder_id else None,
        filename=asset.filename,
        file_url=asset.file_url,
        file_size=asset.file_size,
        mime_type=asset.mime_type,
        width=asset.width,
        height=asset.height,
        title=asset.title,
        description=asset.description,
        tags=asset.tags or [],
        times_used=asset.times_used,
        last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
        created_at=asset.created_at.isoformat(),
    )


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete an asset.

    Args:
        asset_id: Asset UUID

    Returns:
        Success message
    """
    success = asset_service.delete_asset(db, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {"message": "Asset deleted successfully"}


@router.post("/assets/{asset_id}/move", response_model=AssetResponse)
async def move_asset(
    asset_id: str,
    request: MoveAssetRequest,
    db: Session = Depends(get_db),
):
    """
    Move an asset to a different folder.

    Args:
        asset_id: Asset UUID
        request: Move request with target folder ID

    Returns:
        Updated asset
    """
    asset = asset_service.move_asset(db, asset_id, request.target_folder_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return AssetResponse(
        id=str(asset.id),
        tenant_id=str(asset.tenant_id),
        folder_id=str(asset.folder_id) if asset.folder_id else None,
        filename=asset.filename,
        file_url=asset.file_url,
        file_size=asset.file_size,
        mime_type=asset.mime_type,
        width=asset.width,
        height=asset.height,
        title=asset.title,
        description=asset.description,
        tags=asset.tags or [],
        times_used=asset.times_used,
        last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
        created_at=asset.created_at.isoformat(),
    )


@router.get("/assets/search/{tenant_id}", response_model=List[AssetResponse])
async def search_assets(
    tenant_id: str,
    q: str = Query(..., min_length=1),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """
    Search assets by title, description, or tags.

    Args:
        tenant_id: Tenant UUID
        q: Search query
        limit: Max results

    Returns:
        List of matching assets
    """
    assets = asset_service.search_assets(db, tenant_id, q, limit)

    return [
        AssetResponse(
            id=str(asset.id),
            tenant_id=str(asset.tenant_id),
            folder_id=str(asset.folder_id) if asset.folder_id else None,
            filename=asset.filename,
            file_url=asset.file_url,
            file_size=asset.file_size,
            mime_type=asset.mime_type,
            width=asset.width,
            height=asset.height,
            title=asset.title,
            description=asset.description,
            tags=asset.tags or [],
            times_used=asset.times_used,
            last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
            created_at=asset.created_at.isoformat(),
        )
        for asset in assets
    ]


@router.get("/assets/recent/{tenant_id}", response_model=List[AssetResponse])
async def get_recent_assets(
    tenant_id: str,
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    """
    Get recently used assets.

    Args:
        tenant_id: Tenant UUID
        limit: Max results

    Returns:
        List of recently used assets
    """
    assets = asset_service.get_recently_used(db, tenant_id, limit)

    return [
        AssetResponse(
            id=str(asset.id),
            tenant_id=str(asset.tenant_id),
            folder_id=str(asset.folder_id) if asset.folder_id else None,
            filename=asset.filename,
            file_url=asset.file_url,
            file_size=asset.file_size,
            mime_type=asset.mime_type,
            width=asset.width,
            height=asset.height,
            title=asset.title,
            description=asset.description,
            tags=asset.tags or [],
            times_used=asset.times_used,
            last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
            created_at=asset.created_at.isoformat(),
        )
        for asset in assets
    ]


# ==================== Folder Endpoints ====================

@router.post("/folders", response_model=FolderResponse)
async def create_folder(
    request: CreateFolderRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new folder.

    Args:
        request: Folder creation data

    Returns:
        Created folder
    """
    try:
        folder = folder_service.create_folder(
            db=db,
            tenant_id=request.tenant_id,
            name=request.name,
            description=request.description,
            parent_folder_id=request.parent_folder_id,
        )

        return FolderResponse(
            id=str(folder.id),
            tenant_id=str(folder.tenant_id),
            parent_folder_id=str(folder.parent_folder_id) if folder.parent_folder_id else None,
            name=folder.name,
            description=folder.description,
            display_order=folder.display_order,
            is_default=folder.is_default,
            created_at=folder.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")


@router.get("/folders/{tenant_id}")
async def get_folder_tree(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Get folder tree for a tenant.

    Args:
        tenant_id: Tenant UUID

    Returns:
        Folder tree structure
    """
    tree = folder_service.get_folder_tree(db, tenant_id)
    return {"folders": tree}


@router.get("/folders/{folder_id}/details", response_model=FolderResponse)
async def get_folder(
    folder_id: str,
    db: Session = Depends(get_db),
):
    """
    Get folder details.

    Args:
        folder_id: Folder UUID

    Returns:
        Folder details
    """
    folder = folder_service.get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    return FolderResponse(
        id=str(folder.id),
        tenant_id=str(folder.tenant_id),
        parent_folder_id=str(folder.parent_folder_id) if folder.parent_folder_id else None,
        name=folder.name,
        description=folder.description,
        display_order=folder.display_order,
        is_default=folder.is_default,
        created_at=folder.created_at.isoformat(),
    )


@router.patch("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: str,
    request: UpdateFolderRequest,
    db: Session = Depends(get_db),
):
    """
    Update folder properties.

    Args:
        folder_id: Folder UUID
        request: Update data

    Returns:
        Updated folder
    """
    folder = folder_service.update_folder(
        db=db,
        folder_id=folder_id,
        name=request.name,
        description=request.description,
        display_order=request.display_order,
    )

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    return FolderResponse(
        id=str(folder.id),
        tenant_id=str(folder.tenant_id),
        parent_folder_id=str(folder.parent_folder_id) if folder.parent_folder_id else None,
        name=folder.name,
        description=folder.description,
        display_order=folder.display_order,
        is_default=folder.is_default,
        created_at=folder.created_at.isoformat(),
    )


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a folder.

    Args:
        folder_id: Folder UUID

    Returns:
        Success message
    """
    try:
        success = folder_service.delete_folder(db, folder_id)
        if not success:
            raise HTTPException(status_code=404, detail="Folder not found")

        return {"message": "Folder deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")


@router.post("/tenants/{tenant_id}/init-folders")
async def initialize_default_folders(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Create default folders for a tenant.

    Args:
        tenant_id: Tenant UUID

    Returns:
        Created folders
    """
    try:
        folders = folder_service.create_default_folders(db, tenant_id)

        return {
            "message": "Default folders created successfully",
            "folders": [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "description": f.description,
                }
                for f in folders
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create default folders: {str(e)}")
