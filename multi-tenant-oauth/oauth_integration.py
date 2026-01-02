"""
OAuth Integration Layer for Existing Social Media Posting System

This module bridges the multi-tenant OAuth system with your existing posting workflow.
It replaces hardcoded tokens with secure OAuth tokens from the database.
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Add multi-tenant-oauth to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services import TokenService
from app.models.base import SessionLocal
from sqlalchemy.orm import Session


class OAuthTokenManager:
    """
    Manages OAuth tokens for multi-tenant posting system.

    Replaces hardcoded tokens with secure, encrypted tokens from the OAuth database.
    """

    def __init__(self, tenant_id: str = None):
        """
        Initialize OAuth Token Manager.

        Args:
            tenant_id: UUID of the tenant (restaurant). If None, must be provided in method calls.
        """
        self.tenant_id = tenant_id
        self.token_service = TokenService()
        self._db_session: Optional[Session] = None

    def _get_db(self) -> Session:
        """Get or create database session."""
        if self._db_session is None:
            self._db_session = SessionLocal()
        return self._db_session

    def close(self):
        """Close database session."""
        if self._db_session:
            self._db_session.close()
            self._db_session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_facebook_token(self, tenant_id: str = None, account_id: str = None) -> Optional[str]:
        """
        Get decrypted Facebook access token for posting.

        Args:
            tenant_id: Tenant UUID (optional if set in constructor)
            account_id: Specific social account ID (optional - gets first active account)

        Returns:
            Decrypted access token or None if not found

        Example:
            >>> manager = OAuthTokenManager(tenant_id="abc-123")
            >>> token = manager.get_facebook_token()
            >>> # Use token with Facebook Graph API
        """
        tenant = tenant_id or self.tenant_id
        if not tenant:
            raise ValueError("tenant_id must be provided")

        db = self._get_db()

        try:
            token = self.token_service.get_active_token(
                db=db,
                tenant_id=tenant,
                platform="facebook",
                platform_account_id=account_id
            )
            return token
        except Exception as e:
            print(f"Error retrieving Facebook token: {e}")
            return None

    def get_instagram_token(self, tenant_id: str = None, account_id: str = None) -> Optional[str]:
        """
        Get decrypted Instagram access token for posting.

        Args:
            tenant_id: Tenant UUID (optional if set in constructor)
            account_id: Specific social account ID (optional - gets first active account)

        Returns:
            Decrypted access token or None if not found
        """
        tenant = tenant_id or self.tenant_id
        if not tenant:
            raise ValueError("tenant_id must be provided")

        db = self._get_db()

        try:
            token = self.token_service.get_active_token(
                db=db,
                tenant_id=tenant,
                platform="instagram",
                platform_account_id=account_id
            )
            return token
        except Exception as e:
            print(f"Error retrieving Instagram token: {e}")
            return None

    def get_account_info(self, tenant_id: str = None, platform: str = None) -> List[Dict]:
        """
        Get list of connected accounts for a tenant.

        Args:
            tenant_id: Tenant UUID (optional if set in constructor)
            platform: Filter by platform (facebook/instagram) or None for all

        Returns:
            List of account dictionaries with id, platform, name, etc.

        Example:
            >>> manager = OAuthTokenManager(tenant_id="abc-123")
            >>> accounts = manager.get_account_info(platform="facebook")
            >>> for account in accounts:
            ...     print(f"{account['account_name']} - {account['platform']}")
        """
        tenant = tenant_id or self.tenant_id
        if not tenant:
            raise ValueError("tenant_id must be provided")

        db = self._get_db()

        try:
            from app.models import SocialAccount

            query = db.query(SocialAccount).filter(
                SocialAccount.tenant_id == tenant,
                SocialAccount.is_active == True
            )

            if platform:
                query = query.filter(SocialAccount.platform == platform)

            accounts = query.all()

            return [
                {
                    "id": str(account.id),
                    "platform": account.platform,
                    "account_name": account.account_name,
                    "platform_account_id": account.platform_account_id,
                    "platform_username": account.platform_username,
                    "account_type": account.account_type,
                }
                for account in accounts
            ]
        except Exception as e:
            print(f"Error retrieving account info: {e}")
            return []

    def get_token_health(self, tenant_id: str = None) -> Dict:
        """
        Get token health status for a tenant.

        Args:
            tenant_id: Tenant UUID (optional if set in constructor)

        Returns:
            Dictionary with token health statistics
        """
        tenant = tenant_id or self.tenant_id
        if not tenant:
            raise ValueError("tenant_id must be provided")

        db = self._get_db()

        try:
            health = self.token_service.get_tenant_token_health(db, tenant)
            return health
        except Exception as e:
            print(f"Error checking token health: {e}")
            return {
                "total_accounts": 0,
                "active_tokens": 0,
                "expiring_soon": 0,
                "expired": 0
            }


class MultiTenantPosterFactory:
    """
    Factory to create poster instances for specific tenants.

    Integrates OAuth tokens with your existing FacebookPoster and InstagramPoster classes.
    """

    @staticmethod
    def create_facebook_poster(tenant_id: str, account_id: str = None):
        """
        Create a FacebookPoster instance with OAuth token.

        Args:
            tenant_id: Restaurant tenant UUID
            account_id: Specific Facebook Page ID (optional)

        Returns:
            Modified FacebookPoster instance with OAuth token

        Example:
            >>> poster = MultiTenantPosterFactory.create_facebook_poster(
            ...     tenant_id="abc-123"
            ... )
            >>> result = poster.post_photo(image_path, caption="Test post")
        """
        # Import your existing FacebookPoster
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from social_poster import FacebookPoster

        # Create poster instance
        poster = FacebookPoster()

        # Get OAuth token
        with OAuthTokenManager(tenant_id) as manager:
            token = manager.get_facebook_token(account_id=account_id)

            if not token:
                raise ValueError(f"No active Facebook token found for tenant {tenant_id}")

            # Get account info
            accounts = manager.get_account_info(platform="facebook")
            if not accounts:
                raise ValueError(f"No Facebook accounts found for tenant {tenant_id}")

            # Use specific account or first one
            if account_id:
                account = next((a for a in accounts if a["id"] == account_id), None)
                if not account:
                    raise ValueError(f"Account {account_id} not found")
            else:
                account = accounts[0]

            # Override poster credentials with OAuth token
            poster.access_token = token
            poster.page_id = account["platform_account_id"]

        return poster

    @staticmethod
    def create_instagram_poster(tenant_id: str, account_id: str = None):
        """
        Create an InstagramPoster instance with OAuth token.

        Args:
            tenant_id: Restaurant tenant UUID
            account_id: Specific Instagram account ID (optional)

        Returns:
            Modified InstagramPoster instance with OAuth token
        """
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from social_poster import InstagramPoster

        # Create poster instance
        poster = InstagramPoster()

        # Get OAuth token
        with OAuthTokenManager(tenant_id) as manager:
            token = manager.get_instagram_token(account_id=account_id)

            if not token:
                raise ValueError(f"No active Instagram token found for tenant {tenant_id}")

            # Get account info
            accounts = manager.get_account_info(platform="instagram")
            if not accounts:
                raise ValueError(f"No Instagram accounts found for tenant {tenant_id}")

            # Use specific account or first one
            if account_id:
                account = next((a for a in accounts if a["id"] == account_id), None)
                if not account:
                    raise ValueError(f"Account {account_id} not found")
            else:
                account = accounts[0]

            # Override poster credentials with OAuth token
            poster.access_token = token
            poster.instagram_account_id = account["platform_account_id"]

        return poster


# Convenience functions for backward compatibility
def get_facebook_token(tenant_id: str) -> str:
    """
    Simple function to get Facebook token for a tenant.

    Example:
        >>> token = get_facebook_token("abc-123")
    """
    with OAuthTokenManager(tenant_id) as manager:
        return manager.get_facebook_token()


def get_instagram_token(tenant_id: str) -> str:
    """
    Simple function to get Instagram token for a tenant.

    Example:
        >>> token = get_instagram_token("abc-123")
    """
    with OAuthTokenManager(tenant_id) as manager:
        return manager.get_instagram_token()
