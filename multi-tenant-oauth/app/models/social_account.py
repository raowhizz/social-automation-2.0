"""Social media account model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class SocialAccount(Base):
    """Facebook Page or Instagram Business Account model."""

    __tablename__ = "social_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Platform details
    platform = Column(String(50), nullable=False, index=True)
    platform_account_id = Column(String(255), nullable=False)
    platform_username = Column(String(255))
    account_name = Column(String(255))
    account_type = Column(String(50))

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Metadata (profile picture URL, followers count, etc.)
    account_metadata = Column(JSONB, default={})

    # Timestamps
    connected_at = Column(DateTime, default=datetime.utcnow)
    last_sync_at = Column(DateTime)

    # Relationships
    tenant = relationship("Tenant", back_populates="social_accounts")
    oauth_tokens = relationship("OAuthToken", back_populates="social_account", cascade="all, delete-orphan")
    posts = relationship("PostHistory", back_populates="social_account", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "platform IN ('facebook', 'instagram', 'tiktok', 'twitter')",
            name="check_platform",
        ),
        Index(
            "idx_social_accounts_unique",
            "tenant_id",
            "platform",
            "platform_account_id",
            unique=True,
        ),
        Index("idx_social_accounts_tenant_platform", "tenant_id", "platform"),
    )

    def __repr__(self):
        return f"<SocialAccount {self.platform} - {self.account_name or self.platform_username}>"
