"""AssetFolder model for organizing brand assets."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class AssetFolder(Base):
    """Folder for organizing brand assets and images."""

    __tablename__ = "asset_folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Folder hierarchy
    parent_folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("asset_folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Folder properties
    name = Column(String(255), nullable=False)
    description = Column(Text)
    display_order = Column(Integer, default=0)
    is_default = Column(String(1), default='N', nullable=False)  # 'Y' for default folders

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="asset_folders")
    assets = relationship("BrandAsset", back_populates="folder", cascade="all, delete-orphan")

    # Self-referential relationship for folder hierarchy
    parent_folder = relationship(
        "AssetFolder",
        remote_side=[id],
        back_populates="subfolders",
    )
    subfolders = relationship(
        "AssetFolder",
        back_populates="parent_folder",
        cascade="all, delete-orphan",
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_asset_folders_tenant", "tenant_id", "name"),
        Index("idx_asset_folders_parent", "parent_folder_id"),
    )

    def __repr__(self):
        return f"<AssetFolder {self.name} (tenant={self.tenant_id})>"
