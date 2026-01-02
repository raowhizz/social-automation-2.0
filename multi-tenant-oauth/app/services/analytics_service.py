"""Analytics service for engagement metrics."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import requests

from app.models import PostHistory, SocialAccount
from app.services import TokenService


class AnalyticsService:
    """Service for analytics and engagement metrics."""

    def __init__(self):
        """Initialize analytics service."""
        self.token_service = TokenService()

    def get_post_analytics(
        self,
        db: Session,
        tenant_id: str,
        days: int = 30,
        platform: Optional[str] = None,
    ) -> Dict:
        """
        Get posting analytics for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            days: Number of days to analyze
            platform: Optional platform filter

        Returns:
            Analytics dictionary
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Base query
        query = db.query(PostHistory).filter(
            and_(
                PostHistory.tenant_id == tenant_id,
                PostHistory.created_at >= since,
            )
        )

        if platform:
            query = query.filter(PostHistory.platform == platform)

        posts = query.all()

        # Calculate metrics
        total_posts = len(posts)
        published = len([p for p in posts if p.status == "published"])
        failed = len([p for p in posts if p.status == "failed"])
        scheduled = len([p for p in posts if p.status == "scheduled"])
        success_rate = (published / total_posts * 100) if total_posts > 0 else 0

        # Platform breakdown
        platform_stats = {}
        for post in posts:
            if post.platform not in platform_stats:
                platform_stats[post.platform] = {
                    "total": 0,
                    "published": 0,
                    "failed": 0,
                }
            platform_stats[post.platform]["total"] += 1
            if post.status == "published":
                platform_stats[post.platform]["published"] += 1
            elif post.status == "failed":
                platform_stats[post.platform]["failed"] += 1

        # Posts per day
        posts_per_day = total_posts / days if days > 0 else 0

        # Engagement metrics (from stored metrics)
        total_likes = 0
        total_comments = 0
        total_shares = 0

        for post in posts:
            if post.engagement_metrics:
                total_likes += post.engagement_metrics.get("likes", 0)
                total_comments += post.engagement_metrics.get("comments", 0)
                total_shares += post.engagement_metrics.get("shares", 0)

        avg_engagement = (
            (total_likes + total_comments + total_shares) / published
            if published > 0
            else 0
        )

        return {
            "period_days": days,
            "total_posts": total_posts,
            "published": published,
            "failed": failed,
            "scheduled": scheduled,
            "success_rate": round(success_rate, 1),
            "posts_per_day": round(posts_per_day, 1),
            "platform_breakdown": platform_stats,
            "engagement": {
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "avg_engagement": round(avg_engagement, 1),
            },
        }

    def get_time_series_data(
        self,
        db: Session,
        tenant_id: str,
        days: int = 30,
    ) -> List[Dict]:
        """
        Get time series data for charts.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            days: Number of days

        Returns:
            List of daily stats
        """
        since = datetime.utcnow() - timedelta(days=days)

        posts = (
            db.query(PostHistory)
            .filter(
                and_(
                    PostHistory.tenant_id == tenant_id,
                    PostHistory.created_at >= since,
                )
            )
            .all()
        )

        # Group by day
        daily_stats = {}

        for post in posts:
            date = post.created_at.date()
            date_str = date.isoformat()

            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    "date": date_str,
                    "posts": 0,
                    "published": 0,
                    "failed": 0,
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                }

            daily_stats[date_str]["posts"] += 1

            if post.status == "published":
                daily_stats[date_str]["published"] += 1
            elif post.status == "failed":
                daily_stats[date_str]["failed"] += 1

            if post.engagement_metrics:
                daily_stats[date_str]["likes"] += post.engagement_metrics.get("likes", 0)
                daily_stats[date_str]["comments"] += post.engagement_metrics.get(
                    "comments", 0
                )
                daily_stats[date_str]["shares"] += post.engagement_metrics.get(
                    "shares", 0
                )

        # Convert to list and sort by date
        result = sorted(daily_stats.values(), key=lambda x: x["date"])

        return result

    def fetch_facebook_insights(
        self,
        db: Session,
        post_id: str,
    ) -> Optional[Dict]:
        """
        Fetch engagement metrics from Facebook for a post.

        Args:
            db: Database session
            post_id: Post UUID

        Returns:
            Engagement metrics dictionary or None
        """
        post = db.query(PostHistory).filter(PostHistory.id == post_id).first()

        if not post or not post.platform_post_id or post.platform != "facebook":
            return None

        try:
            # Get access token
            access_token = self.token_service.get_active_token(
                db=db,
                tenant_id=str(post.tenant_id),
                platform="facebook",
            )

            if not access_token:
                return None

            # Fetch insights from Facebook
            url = f"https://graph.facebook.com/v18.0/{post.platform_post_id}"
            params = {
                "fields": "likes.summary(true),comments.summary(true),shares",
                "access_token": access_token,
            }

            response = requests.get(url, params=params)
            data = response.json()

            if "error" in data:
                return None

            # Extract metrics
            metrics = {
                "likes": data.get("likes", {}).get("summary", {}).get("total_count", 0),
                "comments": (
                    data.get("comments", {}).get("summary", {}).get("total_count", 0)
                ),
                "shares": data.get("shares", {}).get("count", 0),
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Update post record
            post.engagement_metrics = metrics
            db.commit()

            return metrics

        except Exception as e:
            print(f"Error fetching Facebook insights: {e}")
            return None

    def fetch_instagram_insights(
        self,
        db: Session,
        post_id: str,
    ) -> Optional[Dict]:
        """
        Fetch engagement metrics from Instagram for a post.

        Args:
            db: Database session
            post_id: Post UUID

        Returns:
            Engagement metrics dictionary or None
        """
        post = db.query(PostHistory).filter(PostHistory.id == post_id).first()

        if not post or not post.platform_post_id or post.platform != "instagram":
            return None

        try:
            # Get access token
            access_token = self.token_service.get_active_token(
                db=db,
                tenant_id=str(post.tenant_id),
                platform="instagram",
            )

            if not access_token:
                return None

            # Fetch insights from Instagram
            url = f"https://graph.facebook.com/v18.0/{post.platform_post_id}/insights"
            params = {
                "metric": "engagement,impressions,reach,saved",
                "access_token": access_token,
            }

            response = requests.get(url, params=params)
            data = response.json()

            if "error" in data:
                return None

            # Extract metrics
            metrics_data = {}
            for item in data.get("data", []):
                metrics_data[item["name"]] = item.get("values", [{}])[0].get("value", 0)

            metrics = {
                "engagement": metrics_data.get("engagement", 0),
                "impressions": metrics_data.get("impressions", 0),
                "reach": metrics_data.get("reach", 0),
                "saved": metrics_data.get("saved", 0),
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Update post record
            post.engagement_metrics = metrics
            db.commit()

            return metrics

        except Exception as e:
            print(f"Error fetching Instagram insights: {e}")
            return None

    def get_top_posts(
        self,
        db: Session,
        tenant_id: str,
        limit: int = 10,
        days: int = 30,
    ) -> List[Dict]:
        """
        Get top performing posts by engagement.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            limit: Maximum number of posts
            days: Number of days to look back

        Returns:
            List of top posts
        """
        since = datetime.utcnow() - timedelta(days=days)

        posts = (
            db.query(PostHistory)
            .filter(
                and_(
                    PostHistory.tenant_id == tenant_id,
                    PostHistory.status == "published",
                    PostHistory.posted_at >= since,
                    PostHistory.engagement_metrics != None,
                )
            )
            .all()
        )

        # Calculate total engagement for each post
        posts_with_engagement = []
        for post in posts:
            total_engagement = sum(
                [
                    post.engagement_metrics.get("likes", 0),
                    post.engagement_metrics.get("comments", 0),
                    post.engagement_metrics.get("shares", 0),
                    post.engagement_metrics.get("engagement", 0),
                ]
            )

            posts_with_engagement.append(
                {
                    "id": str(post.id),
                    "platform": post.platform,
                    "caption": post.caption[:100] + "..."
                    if len(post.caption) > 100
                    else post.caption,
                    "posted_at": post.posted_at.isoformat() if post.posted_at else None,
                    "engagement": total_engagement,
                    "metrics": post.engagement_metrics,
                }
            )

        # Sort by engagement and limit
        top_posts = sorted(
            posts_with_engagement, key=lambda x: x["engagement"], reverse=True
        )[:limit]

        return top_posts
