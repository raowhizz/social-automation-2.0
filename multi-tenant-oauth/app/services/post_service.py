"""Post service for managing social media posts and history."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models import PostHistory, SocialAccount
import uuid


class PostService:
    """Service for managing posts and posting history."""

    def create_post_record(
        self,
        db: Session,
        tenant_id: str,
        social_account_id: str,
        platform: str,
        caption: str,
        image_url: Optional[str] = None,
        campaign_name: Optional[str] = None,
        item_name: Optional[str] = None,
        scheduled_for: Optional[datetime] = None,
    ) -> PostHistory:
        """
        Create a post record in history.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            social_account_id: Social account UUID
            platform: Platform name (facebook/instagram)
            caption: Post caption/text
            image_url: Optional image URL
            campaign_name: Optional campaign name
            item_name: Optional item name
            scheduled_for: Optional scheduled time

        Returns:
            Created PostHistory object
        """
        post = PostHistory(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            social_account_id=uuid.UUID(social_account_id),
            platform=platform,
            caption=caption,
            image_url=image_url,
            campaign_name=campaign_name,
            item_name=item_name,
            status="pending" if scheduled_for else "pending",
            scheduled_for=scheduled_for,
        )

        db.add(post)
        db.commit()
        db.refresh(post)
        return post

    def mark_post_published(
        self,
        db: Session,
        post_id: str,
        platform_post_id: str,
    ) -> PostHistory:
        """
        Mark a post as published.

        Args:
            db: Database session
            post_id: Post history UUID
            platform_post_id: Platform's post ID

        Returns:
            Updated PostHistory object
        """
        post = db.query(PostHistory).filter(PostHistory.id == uuid.UUID(post_id)).first()

        if not post:
            raise ValueError(f"Post {post_id} not found")

        post.status = "published"
        post.platform_post_id = platform_post_id
        post.posted_at = datetime.utcnow()

        db.commit()
        db.refresh(post)
        return post

    def mark_post_failed(
        self,
        db: Session,
        post_id: str,
        error_message: str,
    ) -> PostHistory:
        """
        Mark a post as failed.

        Args:
            db: Database session
            post_id: Post history UUID
            error_message: Error message

        Returns:
            Updated PostHistory object
        """
        post = db.query(PostHistory).filter(PostHistory.id == uuid.UUID(post_id)).first()

        if not post:
            raise ValueError(f"Post {post_id} not found")

        post.status = "failed"
        post.error_message = error_message

        db.commit()
        db.refresh(post)
        return post

    def get_recent_posts(
        self,
        db: Session,
        tenant_id: str,
        platform: Optional[str] = None,
        days: int = 30,
        limit: int = 50,
    ) -> List[PostHistory]:
        """
        Get recent posts for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            platform: Optional platform filter
            days: Number of days to look back
            limit: Maximum number of posts

        Returns:
            List of PostHistory objects
        """
        since = datetime.utcnow() - timedelta(days=days)

        query = db.query(PostHistory).filter(
            and_(
                PostHistory.tenant_id == uuid.UUID(tenant_id),
                PostHistory.created_at >= since,
            )
        )

        if platform:
            query = query.filter(PostHistory.platform == platform)

        posts = query.order_by(desc(PostHistory.created_at)).limit(limit).all()

        return posts

    def get_post_captions_for_similarity_check(
        self,
        db: Session,
        tenant_id: str,
        platform: Optional[str] = None,
        days: int = 30,
    ) -> List[str]:
        """
        Get recent post captions for similarity checking.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            platform: Optional platform filter
            days: Number of days to look back

        Returns:
            List of caption strings
        """
        posts = self.get_recent_posts(
            db=db,
            tenant_id=tenant_id,
            platform=platform,
            days=days,
        )

        return [post.caption for post in posts if post.caption]

    def get_tenant_post_stats(
        self,
        db: Session,
        tenant_id: str,
        days: int = 30,
    ) -> Dict:
        """
        Get posting statistics for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            days: Number of days to look back

        Returns:
            Dictionary with stats
        """
        since = datetime.utcnow() - timedelta(days=days)

        posts = db.query(PostHistory).filter(
            and_(
                PostHistory.tenant_id == uuid.UUID(tenant_id),
                PostHistory.created_at >= since,
            )
        ).all()

        total = len(posts)
        published = len([p for p in posts if p.status == "published"])
        failed = len([p for p in posts if p.status == "failed"])
        pending = len([p for p in posts if p.status == "pending"])
        scheduled = len([p for p in posts if p.status == "scheduled"])

        platforms = {}
        for post in posts:
            if post.platform not in platforms:
                platforms[post.platform] = 0
            platforms[post.platform] += 1

        return {
            "total_posts": total,
            "published": published,
            "failed": failed,
            "pending": pending,
            "scheduled": scheduled,
            "by_platform": platforms,
            "days": days,
        }

    def get_post_by_id(
        self,
        db: Session,
        post_id: str,
    ) -> Optional[PostHistory]:
        """
        Get a post by ID.

        Args:
            db: Database session
            post_id: Post UUID

        Returns:
            PostHistory object or None
        """
        return db.query(PostHistory).filter(PostHistory.id == uuid.UUID(post_id)).first()

    def delete_post(
        self,
        db: Session,
        post_id: str,
    ) -> bool:
        """
        Mark a post as deleted.

        Args:
            db: Database session
            post_id: Post UUID

        Returns:
            True if successful
        """
        post = db.query(PostHistory).filter(PostHistory.id == uuid.UUID(post_id)).first()

        if not post:
            return False

        post.status = "deleted"
        db.commit()
        return True
