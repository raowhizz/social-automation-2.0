"""
OAuth Service for Facebook and Instagram OAuth2 flow.
Handles authorization URL generation, callback processing, and token exchange.
"""

import os
import secrets
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode
from sqlalchemy.orm import Session

from app.models import Tenant, SocialAccount, OAuthToken, OAuthState
from app.utils.encryption import get_encryption_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OAuthService:
    """Service for managing OAuth2 flow with Facebook and Instagram."""

    def __init__(self):
        """Initialize OAuth service with Facebook app credentials."""
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI")
        self.graph_api_version = os.getenv("FACEBOOK_GRAPH_API_VERSION", "v18.0")
        self.scopes = os.getenv(
            "FACEBOOK_OAUTH_SCOPES",
            "pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish",
        )

        if not all([self.app_id, self.app_secret, self.redirect_uri]):
            raise ValueError(
                "Missing Facebook OAuth configuration. "
                "Ensure FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, and FACEBOOK_REDIRECT_URI are set."
            )

        self.encryption_service = get_encryption_service()

        # Facebook OAuth URLs
        self.auth_base_url = "https://www.facebook.com"
        self.graph_base_url = f"https://graph.facebook.com/{self.graph_api_version}"

    def generate_authorization_url(
        self,
        db: Session,
        tenant_id: str,
        return_url: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate Facebook OAuth authorization URL.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            return_url: URL to redirect after OAuth completion
            ip_address: User's IP address
            user_agent: User's user agent

        Returns:
            Tuple of (authorization_url, state_token)

        Raises:
            ValueError: If tenant not found
        """
        # Verify tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Generate cryptographic state token
        state_token = secrets.token_urlsafe(32)

        # Store state in database for CSRF protection
        oauth_state = OAuthState(
            state_token=state_token,
            tenant_id=tenant_id,
            return_url=return_url,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(oauth_state)
        db.commit()

        # Build authorization URL
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "state": state_token,
            "scope": self.scopes,
            "response_type": "code",
        }

        authorization_url = f"{self.auth_base_url}/{self.graph_api_version}/dialog/oauth?{urlencode(params)}"

        return authorization_url, state_token

    def handle_callback(
        self,
        db: Session,
        code: str,
        state: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict:
        """
        Handle OAuth callback and exchange code for access token.

        Args:
            db: Database session
            code: Authorization code from Facebook
            state: State token for CSRF protection
            ip_address: User's IP address
            user_agent: User's user agent

        Returns:
            Dict with tenant_id, social_accounts, and return_url

        Raises:
            ValueError: If state is invalid or token exchange fails
        """
        # Verify state token
        oauth_state = (
            db.query(OAuthState)
            .filter(
                OAuthState.state_token == state,
                OAuthState.used == False,
            )
            .first()
        )

        if not oauth_state:
            raise ValueError("Invalid or expired state token")

        if oauth_state.is_expired:
            raise ValueError("State token has expired")

        # Mark state as used
        oauth_state.used = True
        oauth_state.used_at = datetime.utcnow()
        db.commit()

        # Exchange code for access token
        token_url = f"{self.graph_base_url}/oauth/access_token"
        token_params = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }

        response = requests.get(token_url, params=token_params)
        if response.status_code != 200:
            raise ValueError(f"Token exchange failed: {response.text}")

        token_data = response.json()
        user_access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 5184000)  # Default: 60 days

        if not user_access_token:
            raise ValueError("No access token received from Facebook")

        # Get user's Facebook Pages from both personal profile and business portfolios
        logger.info("Fetching pages from /me/accounts (personal profile)")
        personal_pages = self._get_user_pages(user_access_token)

        logger.info("Fetching pages from /me/businesses (business portfolios)")
        business_pages = self._get_business_pages(user_access_token)

        # Merge and deduplicate pages from both sources
        pages = self._merge_pages(personal_pages, business_pages)
        logger.info(f"Total pages to process: {len(pages)}")

        # Store tokens for each page
        social_accounts = []
        for page in pages:
            social_account = self._store_page_token(
                db=db,
                tenant_id=oauth_state.tenant_id,
                page_data=page,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            social_accounts.append(social_account)

        return {
            "tenant_id": str(oauth_state.tenant_id),
            "social_accounts": social_accounts,
            "return_url": oauth_state.return_url,
            "pages_connected": len(social_accounts),
        }

    def _get_user_pages(self, user_access_token: str) -> list:
        """
        Get Facebook Pages managed by the user.

        Args:
            user_access_token: User's Facebook access token

        Returns:
            List of page data dictionaries
        """
        pages_url = f"{self.graph_base_url}/me/accounts"
        params = {
            "access_token": user_access_token,
            "fields": "id,name,access_token,category,instagram_business_account",
        }

        response = requests.get(pages_url, params=params)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch pages: {response.text}")

        data = response.json()
        logger.info(f"Facebook Pages API response: {data}")

        # DEBUG: Write to file to capture response
        import json
        with open("/tmp/facebook_pages_response.json", "w") as f:
            json.dump(data, f, indent=2)

        pages = data.get("data", [])
        logger.info(f"Found {len(pages)} Facebook Pages for user via /me/accounts")
        return pages

    def _get_business_pages(self, user_access_token: str) -> list:
        """
        Get Facebook Pages from Business Manager portfolios.

        Args:
            user_access_token: User's Facebook access token

        Returns:
            List of page data dictionaries
        """
        all_business_pages = []

        try:
            # Get user's businesses
            businesses_url = f"{self.graph_base_url}/me/businesses"
            params = {
                "access_token": user_access_token,
                "fields": "id,name",
            }

            response = requests.get(businesses_url, params=params)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch businesses: {response.text}")
                return []

            businesses_data = response.json()
            businesses = businesses_data.get("data", [])
            logger.info(f"Found {len(businesses)} businesses for user")

            # For each business, get its pages
            for business in businesses:
                business_id = business.get("id")
                business_name = business.get("name")
                logger.info(f"Fetching pages for business: {business_name} (ID: {business_id})")

                # Try client_pages first (pages managed by the business)
                pages_url = f"{self.graph_base_url}/{business_id}/client_pages"
                params = {
                    "access_token": user_access_token,
                    "fields": "id,name,access_token,category,instagram_business_account",
                }

                pages_response = requests.get(pages_url, params=params)
                if pages_response.status_code == 200:
                    pages_data = pages_response.json()
                    pages = pages_data.get("data", [])
                    logger.info(f"Found {len(pages)} pages via client_pages for business {business_name}")
                    all_business_pages.extend(pages)
                else:
                    # Try owned_pages if client_pages doesn't work
                    pages_url = f"{self.graph_base_url}/{business_id}/owned_pages"
                    pages_response = requests.get(pages_url, params=params)
                    if pages_response.status_code == 200:
                        pages_data = pages_response.json()
                        pages = pages_data.get("data", [])
                        logger.info(f"Found {len(pages)} pages via owned_pages for business {business_name}")
                        all_business_pages.extend(pages)
                    else:
                        logger.warning(f"Failed to fetch pages for business {business_name}: {pages_response.text}")

            logger.info(f"Total business pages found: {len(all_business_pages)}")
            return all_business_pages

        except Exception as e:
            logger.error(f"Error fetching business pages: {e}")
            return []

    def _merge_pages(self, personal_pages: list, business_pages: list) -> list:
        """
        Merge and deduplicate pages from personal and business sources.

        Args:
            personal_pages: Pages from /me/accounts
            business_pages: Pages from /me/businesses

        Returns:
            Merged list of unique pages
        """
        seen_page_ids = set()
        merged_pages = []

        # Add personal pages first
        for page in personal_pages:
            page_id = page.get("id")
            if page_id and page_id not in seen_page_ids:
                seen_page_ids.add(page_id)
                merged_pages.append(page)
                logger.debug(f"Added personal page: {page.get('name')} (ID: {page_id})")

        # Add business pages, skipping duplicates
        for page in business_pages:
            page_id = page.get("id")
            if page_id and page_id not in seen_page_ids:
                seen_page_ids.add(page_id)
                merged_pages.append(page)
                logger.debug(f"Added business page: {page.get('name')} (ID: {page_id})")
            else:
                logger.debug(f"Skipped duplicate page: {page.get('name')} (ID: {page_id})")

        logger.info(f"Merged pages: {len(personal_pages)} personal + {len(business_pages)} business = {len(merged_pages)} total unique")
        return merged_pages

    def _store_page_token(
        self,
        db: Session,
        tenant_id: str,
        page_data: Dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict:
        """
        Store Facebook Page token and Instagram account (if connected).

        Args:
            db: Database session
            tenant_id: Tenant UUID
            page_data: Page data from Facebook API
            ip_address: User's IP address
            user_agent: User's user agent

        Returns:
            Dictionary with created social account info
        """
        page_id = page_data["id"]
        page_name = page_data.get("name")
        page_access_token = page_data.get("access_token")
        instagram_account = page_data.get("instagram_business_account")

        # Check if social account already exists
        social_account = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.tenant_id == tenant_id,
                SocialAccount.platform == "facebook",
                SocialAccount.platform_account_id == page_id,
            )
            .first()
        )

        if not social_account:
            # Create new social account
            social_account = SocialAccount(
                tenant_id=tenant_id,
                platform="facebook",
                platform_account_id=page_id,
                account_name=page_name,
                account_type="page",
                metadata={"category": page_data.get("category")},
            )
            db.add(social_account)
            db.flush()  # Get the ID without committing
        else:
            # Reactivate existing account when reconnecting
            social_account.is_active = True
            social_account.account_name = page_name  # Update name in case it changed

        # Get token expiration (Page tokens don't expire but we'll set a far future date)
        expires_at = datetime.utcnow() + timedelta(days=365 * 10)  # 10 years

        # Encrypt the access token
        encrypted_token = self.encryption_service.encrypt(page_access_token)

        # Store or update OAuth token
        oauth_token = (
            db.query(OAuthToken)
            .filter(
                OAuthToken.social_account_id == social_account.id,
                OAuthToken.is_revoked == False,
            )
            .first()
        )

        if oauth_token:
            # Update existing token
            oauth_token.access_token_encrypted = encrypted_token
            oauth_token.last_refreshed_at = datetime.utcnow()
            oauth_token.expires_at = expires_at
        else:
            # Create new token
            oauth_token = OAuthToken(
                social_account_id=social_account.id,
                tenant_id=tenant_id,
                access_token_encrypted=encrypted_token,
                scope=self.scopes,
                expires_at=expires_at,
                client_id=self.app_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(oauth_token)

        db.commit()

        result = {
            "platform": "facebook",
            "account_id": page_id,
            "account_name": page_name,
            "social_account_id": str(social_account.id),
        }

        # Handle Instagram Business Account if connected
        if instagram_account:
            instagram_id = instagram_account.get("id")
            if instagram_id:
                result["instagram"] = self._store_instagram_token(
                    db=db,
                    tenant_id=tenant_id,
                    instagram_id=instagram_id,
                    page_access_token=page_access_token,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

        return result

    def _store_instagram_token(
        self,
        db: Session,
        tenant_id: str,
        instagram_id: str,
        page_access_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict:
        """
        Store Instagram Business Account token.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            instagram_id: Instagram account ID
            page_access_token: Facebook Page access token (used for Instagram)
            ip_address: User's IP address
            user_agent: User's user agent

        Returns:
            Dictionary with Instagram account info
        """
        # Get Instagram account details
        ig_url = f"{self.graph_base_url}/{instagram_id}"
        params = {
            "access_token": page_access_token,
            "fields": "username,name,profile_picture_url",
        }

        response = requests.get(ig_url, params=params)
        if response.status_code != 200:
            # If we can't get Instagram details, skip it
            return None

        ig_data = response.json()
        ig_username = ig_data.get("username")
        ig_name = ig_data.get("name")

        # Check if Instagram account already exists
        social_account = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.tenant_id == tenant_id,
                SocialAccount.platform == "instagram",
                SocialAccount.platform_account_id == instagram_id,
            )
            .first()
        )

        if not social_account:
            # Create new Instagram social account
            social_account = SocialAccount(
                tenant_id=tenant_id,
                platform="instagram",
                platform_account_id=instagram_id,
                platform_username=ig_username,
                account_name=ig_name,
                account_type="business",
                metadata={"profile_picture_url": ig_data.get("profile_picture_url")},
            )
            db.add(social_account)
            db.flush()
        else:
            # Reactivate existing account when reconnecting
            social_account.is_active = True
            social_account.platform_username = ig_username
            social_account.account_name = ig_name
            social_account.metadata = {"profile_picture_url": ig_data.get("profile_picture_url")}

        # Encrypt the access token
        encrypted_token = self.encryption_service.encrypt(page_access_token)

        # Store or update OAuth token
        oauth_token = (
            db.query(OAuthToken)
            .filter(
                OAuthToken.social_account_id == social_account.id,
                OAuthToken.is_revoked == False,
            )
            .first()
        )

        expires_at = datetime.utcnow() + timedelta(days=365 * 10)

        if oauth_token:
            oauth_token.access_token_encrypted = encrypted_token
            oauth_token.last_refreshed_at = datetime.utcnow()
            oauth_token.expires_at = expires_at
        else:
            oauth_token = OAuthToken(
                social_account_id=social_account.id,
                tenant_id=tenant_id,
                access_token_encrypted=encrypted_token,
                scope=self.scopes,
                expires_at=expires_at,
                client_id=self.app_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(oauth_token)

        db.commit()

        return {
            "platform": "instagram",
            "account_id": instagram_id,
            "account_name": ig_name,
            "username": ig_username,
            "social_account_id": str(social_account.id),
        }

    def disconnect_account(self, db: Session, social_account_id: str, tenant_id: str) -> bool:
        """
        Disconnect (revoke) a social media account.

        Args:
            db: Database session
            social_account_id: Social account UUID
            tenant_id: Tenant UUID (for authorization)

        Returns:
            True if successful

        Raises:
            ValueError: If account not found or unauthorized
        """
        # Find social account
        social_account = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.id == social_account_id,
                SocialAccount.tenant_id == tenant_id,
            )
            .first()
        )

        if not social_account:
            raise ValueError("Social account not found or unauthorized")

        # Revoke all tokens for this account
        tokens = (
            db.query(OAuthToken)
            .filter(
                OAuthToken.social_account_id == social_account_id,
                OAuthToken.is_revoked == False,
            )
            .all()
        )

        for token in tokens:
            token.is_revoked = True
            token.revoked_at = datetime.utcnow()
            token.revoked_reason = "User requested disconnect"

        # Deactivate social account
        social_account.is_active = False

        db.commit()

        return True
