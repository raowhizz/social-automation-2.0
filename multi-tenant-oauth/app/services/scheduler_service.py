"""Post scheduling service using Celery."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models import PostHistory
from app.services import PostService, TokenService
import requests
import uuid


class SchedulerService:
    """Service for scheduling social media posts."""

    def __init__(self):
        """Initialize scheduler service."""
        self.post_service = PostService()
        self.token_service = TokenService()

    def schedule_post(
        self,
        db: Session,
        tenant_id: str,
        social_account_id: str,
        platform: str,
        caption: str,
        image_url: Optional[str],
        scheduled_for: datetime,
        campaign_name: Optional[str] = None,
        item_name: Optional[str] = None,
    ) -> PostHistory:
        """
        Schedule a post for future publication.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            social_account_id: Social account UUID
            platform: Platform name
            caption: Post caption
            image_url: Optional image URL
            scheduled_for: When to publish
            campaign_name: Optional campaign name
            item_name: Optional item name

        Returns:
            PostHistory object
        """
        # Create post record with scheduled status
        post = self.post_service.create_post_record(
            db=db,
            tenant_id=tenant_id,
            social_account_id=social_account_id,
            platform=platform,
            caption=caption,
            image_url=image_url,
            campaign_name=campaign_name,
            item_name=item_name,
            scheduled_for=scheduled_for,
        )

        # Update status to scheduled
        post.status = "scheduled"
        db.commit()
        db.refresh(post)

        # Schedule Celery task (if Celery is available)
        try:
            from app.tasks import publish_scheduled_post

            # Calculate delay
            delay_seconds = (scheduled_for - datetime.utcnow()).total_seconds()

            if delay_seconds > 0:
                # Schedule the task
                publish_scheduled_post.apply_async(
                    args=[str(post.id)],
                    countdown=int(delay_seconds),
                )
        except (ImportError, Exception) as e:
            print(f"Celery scheduling not available: {e}")
            # Post will be picked up by periodic task

        return post

    def get_due_posts(self, db: Session, limit: int = 100) -> list[PostHistory]:
        """
        Get posts that are due to be published.

        Args:
            db: Database session
            limit: Maximum number of posts

        Returns:
            List of PostHistory objects
        """
        now = datetime.utcnow()

        posts = (
            db.query(PostHistory)
            .filter(
                PostHistory.status == "scheduled",
                PostHistory.scheduled_for <= now,
            )
            .order_by(PostHistory.scheduled_for)
            .limit(limit)
            .all()
        )

        return posts

    def publish_post(
        self,
        db: Session,
        post_id: str,
    ) -> bool:
        """
        Publish a scheduled post immediately.

        Args:
            db: Database session
            post_id: Post UUID

        Returns:
            True if successful
        """
        post = self.post_service.get_post_by_id(db, post_id)

        if not post:
            return False

        if post.status != "scheduled":
            return False

        try:
            # Get OAuth token
            access_token = self.token_service.get_active_token(
                db=db,
                tenant_id=str(post.tenant_id),
                platform=post.platform,
            )

            if not access_token:
                raise Exception("No active OAuth token found")

            # Get social account
            from app.models import SocialAccount

            social_account = (
                db.query(SocialAccount)
                .filter(SocialAccount.id == post.social_account_id)
                .first()
            )

            if not social_account:
                raise Exception("Social account not found")

            # Post to platform
            if post.platform == "facebook":
                platform_post_id = self._post_to_facebook(
                    page_id=social_account.platform_account_id,
                    access_token=access_token,
                    caption=post.caption,
                    image_url=post.image_url,
                )
            elif post.platform == "instagram":
                platform_post_id = self._post_to_instagram(
                    instagram_account_id=social_account.platform_account_id,
                    access_token=access_token,
                    caption=post.caption,
                    image_url=post.image_url,
                )
            else:
                raise Exception(f"Unsupported platform: {post.platform}")

            # Mark as published
            self.post_service.mark_post_published(
                db=db,
                post_id=post_id,
                platform_post_id=platform_post_id,
            )

            return True

        except Exception as e:
            # Mark as failed
            self.post_service.mark_post_failed(
                db=db,
                post_id=post_id,
                error_message=str(e),
            )
            return False

    def cancel_scheduled_post(
        self,
        db: Session,
        post_id: str,
    ) -> bool:
        """
        Cancel a scheduled post.

        Args:
            db: Database session
            post_id: Post UUID

        Returns:
            True if successful
        """
        post = self.post_service.get_post_by_id(db, post_id)

        if not post or post.status != "scheduled":
            return False

        post.status = "deleted"
        db.commit()

        return True

    # Helper methods
    def _post_to_facebook(
        self,
        page_id: str,
        access_token: str,
        caption: str,
        image_url: Optional[str] = None,
    ) -> str:
        """Post to Facebook and return post ID."""
        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"

        data = {
            "message": caption,
            "access_token": access_token,
        }

        if image_url:
            url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
            data["url"] = image_url
            data["caption"] = caption
            del data["message"]

        response = requests.post(url, data=data)
        result = response.json()

        if "id" in result:
            return result["id"]
        elif "error" in result:
            raise Exception(result["error"].get("message", "Unknown error"))
        else:
            raise Exception("Failed to post to Facebook")

    def _post_to_instagram(
        self,
        instagram_account_id: str,
        access_token: str,
        caption: str,
        image_url: Optional[str] = None,
    ) -> str:
        """Post to Instagram and return media ID."""
        if not image_url:
            raise Exception("Instagram posts require an image")

        # Step 1: Create container
        container_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media"
        container_data = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        }

        response = requests.post(container_url, data=container_data)
        result = response.json()

        if "id" not in result:
            error = result.get("error", {})
            raise Exception(
                error.get("message", "Failed to create Instagram container")
            )

        container_id = result["id"]

        # Step 2: Publish container
        publish_url = (
            f"https://graph.facebook.com/v18.0/{instagram_account_id}/media_publish"
        )
        publish_data = {
            "creation_id": container_id,
            "access_token": access_token,
        }

        response = requests.post(publish_url, data=publish_data)
        result = response.json()

        if "id" in result:
            return result["id"]
        elif "error" in result:
            raise Exception(
                result["error"].get("message", "Failed to publish Instagram post")
            )
        else:
            raise Exception("Failed to publish to Instagram")
