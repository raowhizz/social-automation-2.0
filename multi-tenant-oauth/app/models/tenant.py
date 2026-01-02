"""Tenant and TenantUser models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, CheckConstraint, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class Tenant(Base):
    """Restaurant/business tenant model."""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))

    status = Column(
        String(20),
        default="active",
        nullable=False,
        index=True,
    )
    plan_type = Column(
        String(50),
        default="basic",
        nullable=False,
    )

    # Metadata
    tenant_metadata = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    social_accounts = relationship("SocialAccount", back_populates="tenant", cascade="all, delete-orphan")
    oauth_tokens = relationship("OAuthToken", back_populates="tenant", cascade="all, delete-orphan")
    posts = relationship("PostHistory", back_populates="tenant", cascade="all, delete-orphan")
    oauth_states = relationship("OAuthState", back_populates="tenant", cascade="all, delete-orphan")
    asset_folders = relationship("AssetFolder", back_populates="tenant", cascade="all, delete-orphan")
    brand_assets = relationship("BrandAsset", back_populates="tenant", cascade="all, delete-orphan")
    restaurant_profile = relationship("RestaurantProfile", back_populates="tenant", cascade="all, delete-orphan", uselist=False)
    menu_items = relationship("MenuItem", back_populates="tenant", cascade="all, delete-orphan")
    sales_data = relationship("SalesData", back_populates="tenant", cascade="all, delete-orphan")
    content_calendars = relationship("ContentCalendar", back_populates="tenant", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended', 'trial', 'churned')",
            name="check_tenant_status",
        ),
        CheckConstraint(
            "plan_type IN ('basic', 'pro', 'enterprise')",
            name="check_plan_type",
        ),
        CheckConstraint(
            "slug ~ '^[a-z0-9_]+$'",
            name="check_slug_format",
        ),
    )

    def __repr__(self):
        return f"<Tenant {self.slug} ({self.name})>"


class TenantUser(Base):
    """Restaurant admin/staff user model."""

    __tablename__ = "tenant_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255))

    role = Column(
        String(50),
        default="admin",
        nullable=False,
    )

    # Authentication (for future)
    password_hash = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('owner', 'admin', 'manager', 'staff')",
            name="check_user_role",
        ),
        Index("idx_tenant_users_unique", "tenant_id", "email", unique=True),
    )

    def __repr__(self):
        return f"<TenantUser {self.email} ({self.role})>"
