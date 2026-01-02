"""
Token Management Service.
Handles token retrieval, refresh, validation, and caching.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Tenant, SocialAccount, OAuthToken, TokenRefreshHistory
from app.utils.encryption import get_encryption_service


class TokenService:
    """Service for managing OAuth tokens lifecycle."""

    def __init__(self):
        """Initialize token service."""
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.graph_api_version = os.getenv("FACEBOOK_GRAPH_API_VERSION", "v18.0")
        self.graph_base_url = f"https://graph.facebook.com/{self.graph_api_version}"

        # Token refresh threshold (default: 7 days before expiration)
        self.refresh_threshold_days = int(os.getenv("TOKEN_REFRESH_THRESHOLD_DAYS", "7"))

        self.encryption_service = get_encryption_service()

    def get_active_token(
        self,
        db: Session,
        tenant_id: str,
        platform: str,
        platform_account_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get an active (decrypted) access token for a tenant's social account.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            platform: Platform name (facebook, instagram)
            platform_account_id: Specific account ID (optional)

        Returns:
            Decrypted access token or None if not found

        Raises:
            ValueError: If token is expired or revoked
        """
        # Build query
        query = (
            db.query(OAuthToken)
            .join(SocialAccount)
            .filter(
                and_(
                    SocialAccount.tenant_id == tenant_id,
                    SocialAccount.platform == platform,
                    SocialAccount.is_active == True,
                    OAuthToken.is_revoked == False,
                )
            )
        )

        if platform_account_id:
            query = query.filter(SocialAccount.platform_account_id == platform_account_id)

        # Get the most recent token
        oauth_token = query.order_by(OAuthToken.issued_at.desc()).first()

        if not oauth_token:
            return None

        # Check if token is expired
        if oauth_token.is_expired:
            # Try to refresh it
            refreshed = self.refresh_token(db, oauth_token.id)
            if not refreshed:
                raise ValueError("Token is expired and refresh failed")

            # Re-fetch the token after refresh
            oauth_token = db.query(OAuthToken).filter(OAuthToken.id == oauth_token.id).first()

        # Update last used timestamp
        oauth_token.last_used_at = datetime.utcnow()
        db.commit()

        # Decrypt and return token
        try:
            decrypted_token = self.encryption_service.decrypt(oauth_token.access_token_encrypted)
            return decrypted_token
        except Exception as e:
            raise ValueError(f"Failed to decrypt token: {e}")

    def refresh_token(self, db: Session, token_id: str) -> bool:
        """
        Refresh an OAuth token.

        Args:
            db: Database session
            token_id: OAuth token UUID

        Returns:
            True if refresh successful, False otherwise
        """
        oauth_token = db.query(OAuthToken).filter(OAuthToken.id == token_id).first()

        if not oauth_token:
            return False

        if oauth_token.is_revoked:
            return False

        # Facebook Page tokens don't expire, but we'll verify they're still valid
        # For user tokens, we would use the refresh token here
        decrypted_token = self.encryption_service.decrypt(oauth_token.access_token_encrypted)

        # Verify token is still valid
        is_valid = self._verify_token(decrypted_token)

        old_expires_at = oauth_token.expires_at

        if is_valid:
            # Token is still valid, update expiration
            new_expires_at = datetime.utcnow() + timedelta(days=365)
            oauth_token.expires_at = new_expires_at
            oauth_token.last_refreshed_at = datetime.utcnow()

            # Record refresh history
            refresh_history = TokenRefreshHistory(
                oauth_token_id=token_id,
                tenant_id=oauth_token.tenant_id,
                old_expires_at=old_expires_at,
                new_expires_at=new_expires_at,
                refresh_status="success",
            )
            db.add(refresh_history)
            db.commit()

            return True
        else:
            # Token is invalid, mark as revoked
            oauth_token.is_revoked = True
            oauth_token.revoked_at = datetime.utcnow()
            oauth_token.revoked_reason = "Token verification failed"

            # Record refresh history
            refresh_history = TokenRefreshHistory(
                oauth_token_id=token_id,
                tenant_id=oauth_token.tenant_id,
                old_expires_at=old_expires_at,
                new_expires_at=None,
                refresh_status="failed",
                error_message="Token verification failed",
            )
            db.add(refresh_history)
            db.commit()

            return False

    def _verify_token(self, access_token: str) -> bool:
        """
        Verify if an access token is still valid.

        Args:
            access_token: Facebook access token

        Returns:
            True if valid, False otherwise
        """
        debug_url = f"{self.graph_base_url}/debug_token"
        params = {
            "input_token": access_token,
            "access_token": f"{self.app_id}|{self.app_secret}",
        }

        try:
            response = requests.get(debug_url, params=params, timeout=10)
            if response.status_code != 200:
                return False

            data = response.json()
            token_data = data.get("data", {})

            # Check if token is valid
            is_valid = token_data.get("is_valid", False)
            return is_valid

        except Exception:
            return False

    def get_tokens_expiring_soon(self, db: Session, days: int = None) -> list:
        """
        Get tokens that are expiring soon.

        Args:
            db: Database session
            days: Number of days threshold (default: TOKEN_REFRESH_THRESHOLD_DAYS)

        Returns:
            List of OAuthToken objects expiring soon
        """
        if days is None:
            days = self.refresh_threshold_days

        threshold_date = datetime.utcnow() + timedelta(days=days)

        tokens = (
            db.query(OAuthToken)
            .filter(
                and_(
                    OAuthToken.is_revoked == False,
                    OAuthToken.expires_at != None,
                    OAuthToken.expires_at <= threshold_date,
                )
            )
            .all()
        )

        return tokens

    def refresh_expiring_tokens(self, db: Session) -> Dict:
        """
        Refresh all tokens that are expiring soon.

        Args:
            db: Database session

        Returns:
            Dictionary with refresh statistics
        """
        tokens = self.get_tokens_expiring_soon(db)

        stats = {
            "total": len(tokens),
            "success": 0,
            "failed": 0,
            "errors": [],
        }

        for token in tokens:
            try:
                success = self.refresh_token(db, str(token.id))
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    stats["errors"].append(
                        {
                            "token_id": str(token.id),
                            "tenant_id": str(token.tenant_id),
                            "error": "Refresh failed",
                        }
                    )
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(
                    {
                        "token_id": str(token.id),
                        "tenant_id": str(token.tenant_id),
                        "error": str(e),
                    }
                )

        return stats

    def get_tenant_token_health(self, db: Session, tenant_id: str) -> Dict:
        """
        Get token health status for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID

        Returns:
            Dictionary with token health statistics
        """
        # Get all active tokens for tenant
        active_tokens = (
            db.query(OAuthToken)
            .filter(
                and_(
                    OAuthToken.tenant_id == tenant_id,
                    OAuthToken.is_revoked == False,
                )
            )
            .all()
        )

        # Get social accounts
        social_accounts = (
            db.query(SocialAccount)
            .filter(
                and_(
                    SocialAccount.tenant_id == tenant_id,
                    SocialAccount.is_active == True,
                )
            )
            .all()
        )

        # Count expiring soon
        expiring_soon = sum(
            1
            for token in active_tokens
            if token.expires_at
            and token.expires_at
            <= (datetime.utcnow() + timedelta(days=self.refresh_threshold_days))
        )

        # Count expired
        expired = sum(1 for token in active_tokens if token.is_expired)

        return {
            "tenant_id": tenant_id,
            "total_accounts": len(social_accounts),
            "active_tokens": len(active_tokens),
            "expiring_soon": expiring_soon,
            "expired": expired,
            "healthy": len(active_tokens) - expired - expiring_soon,
            "accounts_by_platform": {
                "facebook": sum(1 for acc in social_accounts if acc.platform == "facebook"),
                "instagram": sum(1 for acc in social_accounts if acc.platform == "instagram"),
            },
        }
