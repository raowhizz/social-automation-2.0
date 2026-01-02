"""BrandAsset model for storing uploaded images and media."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Index, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class BrandAsset(Base):
    """Brand asset (image/media) model."""

    __tablename__ = "brand_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("asset_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative path from upload dir
    file_url = Column(Text, nullable=False)  # Public URL
    file_size = Column(BigInteger)  # Size in bytes
    mime_type = Column(String(100))  # e.g., "image/jpeg"

    # Image dimensions
    width = Column(Integer)
    height = Column(Integer)

    # Metadata
    title = Column(String(255))
    description = Column(Text)
    tags = Column(JSONB, default=[])  # Array of tag strings
    asset_metadata = Column(JSONB, default={})  # Additional flexible metadata

    # Usage tracking
    times_used = Column(Integer, default=0)  # How many posts used this asset
    last_used_at = Column(DateTime)  # When last used in a post

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="brand_assets")
    folder = relationship("AssetFolder", back_populates="assets")
    # Note: PostHistory relationship will be added if we implement usage tracking

    # Indexes for performance
    __table_args__ = (
        Index("idx_brand_assets_tenant", "tenant_id", "created_at"),
        Index("idx_brand_assets_folder", "folder_id"),
        Index("idx_brand_assets_tags", "tags", postgresql_using="gin"),  # GIN index for JSONB
    )

    def __repr__(self):
        return f"<BrandAsset {self.filename} (tenant={self.tenant_id})>"
