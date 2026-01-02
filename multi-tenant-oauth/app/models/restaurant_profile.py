"""RestaurantProfile model for storing restaurant intelligence data."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class RestaurantProfile(Base):
    """Restaurant profile with AI-generated brand analysis."""

    __tablename__ = "restaurant_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic restaurant information
    name = Column(String(255))
    cuisine_type = Column(String(100))
    location = Column(JSONB)  # {"address": "...", "city": "...", "state": "...", "zip": "..."}
    website = Column(String(500))
    phone = Column(String(20))

    # AI-generated intelligence
    brand_analysis = Column(JSONB)  # Brand personality, voice, themes, tone
    sales_insights = Column(JSONB)  # Slow days, peak hours, bestsellers, trends
    content_strategy = Column(JSONB)  # What to post, when to post, content themes

    # Import metadata
    last_menu_import = Column(DateTime)
    last_sales_import = Column(DateTime)
    menu_items_count = Column(Integer, default=0)
    sales_records_count = Column(Integer, default=0)

    # Feature flags
    show_prompt_previews = Column(Boolean, default=False, nullable=False)
    use_ai_for_all_posts = Column(Boolean, default=False, nullable=False)  # Force AI for all posts vs template mix

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="restaurant_profile")

    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_restaurant_profiles_tenant_id"),
        Index("ix_restaurant_profiles_tenant_id", "tenant_id"),
    )

    def __repr__(self):
        return f"<RestaurantProfile {self.name} (tenant={self.tenant_id})>"
