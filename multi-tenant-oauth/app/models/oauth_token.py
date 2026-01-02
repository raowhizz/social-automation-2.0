"""OAuth token models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from .base import Base


class OAuthToken(Base):
    """OAuth access/refresh token model (encrypted storage)."""

    __tablename__ = "oauth_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    social_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token data (ENCRYPTED before storage)
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text)
    token_type = Column(String(50), default="Bearer")

    # Token metadata
    scope = Column(Text)
    issued_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, index=True)
    last_refreshed_at = Column(DateTime)
    last_used_at = Column(DateTime, index=True)

    # Security
    client_id = Column(String(255))
    token_version = Column(Integer, default=1)
    is_revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(DateTime)
    revoked_reason = Column(Text)

    # Audit
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("tenant_users.id"))
    ip_address = Column(INET)
    user_agent = Column(Text)

    # Relationships
    social_account = relationship("SocialAccount", back_populates="oauth_tokens")
    tenant = relationship("Tenant", back_populates="oauth_tokens")
    refresh_history = relationship(
        "TokenRefreshHistory",
        back_populates="oauth_token",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_oauth_tokens_active",
            "tenant_id",
            "is_revoked",
            postgresql_where=(is_revoked == False),
        ),
        Index(
            "idx_oauth_tokens_expires",
            "expires_at",
            postgresql_where=(expires_at != None),
        ),
    )

    def __repr__(self):
        return f"<OAuthToken {self.id} (revoked={self.is_revoked})>"

    @property
    def is_expired(self):
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Check if token is valid (not revoked and not expired)."""
        return not self.is_revoked and not self.is_expired


class TokenRefreshHistory(Base):
    """Token refresh audit trail."""

    __tablename__ = "token_refresh_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    oauth_token_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oauth_tokens.id", ondelete="CASCADE"),
        index=True,
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
    )

    # Refresh details
    refreshed_at = Column(DateTime, default=datetime.utcnow)
    old_expires_at = Column(DateTime)
    new_expires_at = Column(DateTime)
    refresh_status = Column(String(50))
    error_message = Column(Text)

    # Relationships
    oauth_token = relationship("OAuthToken", back_populates="refresh_history")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "refresh_status IN ('success', 'failed', 'revoked')",
            name="check_refresh_status",
        ),
        Index("idx_token_refresh_tenant_date", "tenant_id", "refreshed_at"),
    )

    def __repr__(self):
        return f"<TokenRefreshHistory {self.refresh_status} at {self.refreshed_at}>"
