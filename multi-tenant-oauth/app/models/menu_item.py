"""MenuItem model for storing restaurant menu data."""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Boolean, Date, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class MenuItem(Base):
    """Menu item model with popularity tracking."""

    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Item identification (from POS)
    external_id = Column(String(50))  # ID from Innowi POS
    category = Column(String(255))  # e.g., "Pizza", "Pasta", "Appetizers"
    name = Column(String(500), nullable=False)
    description = Column(Text)
    image_url = Column(Text)

    # Link to brand asset (if image was synced to asset library)
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("brand_assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Pricing
    price = Column(Numeric(10, 2))
    cost = Column(Numeric(10, 2))  # Cost of goods if available

    # Modifiers
    has_modifiers = Column(Boolean, default=False)
    modifiers = Column(JSONB)  # Array of modifier groups with options

    # Special flags
    is_deal = Column(Boolean, default=False)  # Is this a combo/deal?
    out_of_stock = Column(Boolean, default=False)

    # Popularity tracking
    times_ordered = Column(Integer, default=0)  # Updated from sales data
    total_revenue = Column(Numeric(10, 2), default=0)  # Total revenue from this item
    popularity_rank = Column(Integer)  # 1 = most popular

    # Social media tracking
    times_posted_about = Column(Integer, default=0)  # How many posts featured this item
    last_featured_date = Column(Date)  # When was it last posted about

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="menu_items")
    asset = relationship("BrandAsset", foreign_keys=[asset_id])

    # Indexes for performance
    __table_args__ = (
        Index("ix_menu_items_tenant_id", "tenant_id"),
        Index("ix_menu_items_tenant_category", "tenant_id", "category"),
        Index("ix_menu_items_tenant_popularity", "tenant_id", "popularity_rank"),
    )

    def __repr__(self):
        return f"<MenuItem {self.name} (category={self.category}, tenant={self.tenant_id})>"
