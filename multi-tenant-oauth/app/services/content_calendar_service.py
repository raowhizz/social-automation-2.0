"""Content Calendar Service - Generate monthly post calendars with strategic distribution."""

from typing import Dict, List, Any
import uuid
import calendar
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
import logging
import requests

from app.models import (
    ContentCalendar,
    CalendarPost,
    RestaurantProfile,
    MenuItem,
    SocialAccount,
)
from app.services.post_suggestion_service import PostSuggestionService
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)


class ContentCalendarService:
    """Generate and manage monthly content calendars."""

    def __init__(self):
        """Initialize content calendar service."""
        self.suggestion_service = PostSuggestionService()
        self.token_service = TokenService()

    async def generate_monthly_calendar(
        self,
        db: Session,
        tenant_id: str,
        year: int,
        month: int,
        posts_count: int = 25,
    ) -> Dict[str, Any]:
        """
        Generate a monthly content calendar with strategically distributed posts.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            year: Calendar year
            month: Calendar month (1-12)
            posts_count: Number of posts to generate (default 25)

        Returns:
            Dict with calendar and posts data
        """
        try:
            # Check if calendar already exists
            existing = db.query(ContentCalendar).filter(
                ContentCalendar.tenant_id == uuid.UUID(tenant_id),
                ContentCalendar.year == year,
                ContentCalendar.month == month,
            ).first()

            if existing:
                return {
                    "success": False,
                    "error": f"Calendar for {year}-{month:02d} already exists. Delete it first to regenerate."
                }

            # Get restaurant profile for context
            profile = db.query(RestaurantProfile).filter(
                RestaurantProfile.tenant_id == uuid.UUID(tenant_id)
            ).first()

            if not profile:
                return {
                    "success": False,
                    "error": "Restaurant profile not found. Please complete setup first."
                }

            # Create calendar
            content_calendar = ContentCalendar(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                year=year,
                month=month,
                status="draft",
                total_posts=0,
                generated_at=datetime.utcnow(),
            )
            db.add(content_calendar)
            db.flush()  # Get calendar ID

            # Generate posts
            posts = await self._generate_calendar_posts(
                db,
                tenant_id,
                content_calendar.id,
                year,
                month,
                posts_count,
                profile,
            )

            # Update calendar totals
            content_calendar.total_posts = len(posts)
            db.commit()

            logger.info(f"Generated calendar {content_calendar.id} with {len(posts)} posts for {year}-{month:02d}")

            return {
                "success": True,
                "calendar_id": str(content_calendar.id),
                "year": year,
                "month": month,
                "total_posts": len(posts),
                "posts": [self._serialize_post(post) for post in posts],
            }

        except Exception as e:
            logger.error(f"Error generating monthly calendar: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def _generate_calendar_posts(
        self,
        db: Session,
        tenant_id: str,
        calendar_id: uuid.UUID,
        year: int,
        month: int,
        posts_count: int,
        profile: RestaurantProfile,
    ) -> List[CalendarPost]:
        """Generate posts for the calendar with strategic distribution."""
        posts = []

        # Get month details
        month_days = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)

        # Get sales insights for strategic scheduling
        sales_insights = profile.sales_insights or {}
        sales_patterns = sales_insights.get('sales_patterns', {})
        slowest_days = sales_patterns.get('slowest_days', [])
        busiest_days = sales_patterns.get('busiest_days', [])

        # Generate varied suggestions
        suggestions_result = await self.suggestion_service.generate_suggestions(
            db, tenant_id, count=posts_count
        )

        if not suggestions_result.get('success'):
            logger.warning(f"Failed to generate suggestions: {suggestions_result.get('error')}")
            return posts

        suggestions = suggestions_result.get('suggestions', [])

        # Distribute posts across the month
        days_to_post = self._calculate_posting_schedule(month_days, len(suggestions))

        for i, suggestion in enumerate(suggestions):
            if i >= len(days_to_post):
                break

            day_number = days_to_post[i]
            post_date = date(year, month, day_number)
            day_name = post_date.strftime('%A')

            # Determine optimal posting time based on post type and day
            post_time = self._get_optimal_posting_time(
                suggestion.get('type'),
                day_name,
                slowest_days,
                busiest_days,
            )

            # Get image for post (hybrid: assets first, then AI)
            asset_id, image_url = await self.suggestion_service._get_post_image(
                db=db,
                tenant_id=tenant_id,
                post_type=suggestion.get('type', 'general'),
                featured_items=suggestion.get('featured_items', []),
                post_text=suggestion.get('post_text', ''),
                profile=profile,
            )

            # Create calendar post
            calendar_post = CalendarPost(
                id=uuid.uuid4(),
                calendar_id=calendar_id,
                tenant_id=uuid.UUID(tenant_id),
                post_type=suggestion.get('type', 'general'),
                title=suggestion.get('title', 'Untitled Post'),
                post_text=suggestion.get('post_text', ''),
                scheduled_date=post_date,
                scheduled_time=post_time,
                platform="both",  # Default to both platforms
                status="draft",
                image_url=image_url,
                asset_id=asset_id,
                featured_items=suggestion.get('featured_items', []),
                hashtags=suggestion.get('hashtags', []),
                call_to_action=suggestion.get('call_to_action'),
                reason=suggestion.get('reason'),
                generated_by=suggestion.get('generated_by', 'template'),
            )

            posts.append(calendar_post)
            db.add(calendar_post)

        db.flush()
        return posts

    def _calculate_posting_schedule(self, month_days: int, posts_count: int) -> List[int]:
        """
        Calculate which days to post on for even distribution.

        Args:
            month_days: Number of days in the month
            posts_count: Number of posts to distribute

        Returns:
            List of day numbers (1-31) to post on
        """
        if posts_count >= month_days:
            # Post every day
            return list(range(1, month_days + 1))

        # Distribute posts evenly across the month
        interval = month_days / posts_count
        days = []

        for i in range(posts_count):
            day = int((i * interval) + 1)
            if day > month_days:
                day = month_days
            if day not in days:
                days.append(day)

        return sorted(days)

    def _get_optimal_posting_time(
        self,
        post_type: str,
        day_name: str,
        slowest_days: List[str],
        busiest_days: List[str],
    ) -> time:
        """
        Determine optimal posting time based on post type and day.

        Args:
            post_type: Type of post
            day_name: Day of week name
            slowest_days: List of slowest days
            busiest_days: List of busiest days

        Returns:
            Time object for posting
        """
        # Promotional posts on slow days - post early (10 AM)
        if post_type == "promotional" or day_name in slowest_days:
            return time(10, 0)

        # Weekend driver posts on Friday - post late afternoon (5 PM)
        if post_type == "weekend_traffic" or day_name == "Friday":
            return time(17, 0)

        # Product showcase - dinner time (6 PM)
        if post_type == "product_showcase":
            return time(18, 0)

        # Engagement posts - mid-day for better engagement (12 PM)
        if post_type == "engagement":
            return time(12, 0)

        # Customer appreciation - afternoon (3 PM)
        if post_type == "customer_appreciation":
            return time(15, 0)

        # Default: lunch time (12 PM)
        return time(12, 0)

    def _serialize_post(self, post: CalendarPost) -> Dict[str, Any]:
        """Serialize calendar post to dict."""
        return {
            "id": str(post.id),
            "post_type": post.post_type,
            "title": post.title,
            "post_text": post.post_text,
            "scheduled_date": post.scheduled_date.isoformat(),
            "scheduled_time": post.scheduled_time.isoformat(),
            "platform": post.platform,
            "status": post.status,
            "image_url": post.image_url,
            "asset_id": str(post.asset_id) if post.asset_id else None,
            "featured_items": post.featured_items,
            "hashtags": post.hashtags,
            "call_to_action": post.call_to_action,
            "reason": post.reason,
            "generated_by": post.generated_by,
        }

    async def get_calendar(
        self,
        db: Session,
        tenant_id: str,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """Get calendar for a specific month."""
        try:
            content_calendar = db.query(ContentCalendar).filter(
                ContentCalendar.tenant_id == uuid.UUID(tenant_id),
                ContentCalendar.year == year,
                ContentCalendar.month == month,
            ).first()

            if not content_calendar:
                return {
                    "success": False,
                    "error": f"No calendar found for {year}-{month:02d}"
                }

            posts = db.query(CalendarPost).filter(
                CalendarPost.calendar_id == content_calendar.id
            ).order_by(CalendarPost.scheduled_date, CalendarPost.scheduled_time).all()

            return {
                "success": True,
                "calendar": {
                    "id": str(content_calendar.id),
                    "year": content_calendar.year,
                    "month": content_calendar.month,
                    "status": content_calendar.status,
                    "total_posts": content_calendar.total_posts,
                    "approved_posts": content_calendar.approved_posts,
                    "published_posts": content_calendar.published_posts,
                },
                "posts": [self._serialize_post(post) for post in posts],
            }

        except Exception as e:
            logger.error(f"Error getting calendar: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def approve_calendar(
        self,
        db: Session,
        calendar_id: str,
    ) -> Dict[str, Any]:
        """Approve all posts in a calendar."""
        try:
            content_calendar = db.query(ContentCalendar).filter(
                ContentCalendar.id == uuid.UUID(calendar_id)
            ).first()

            if not content_calendar:
                return {
                    "success": False,
                    "error": "Calendar not found"
                }

            # Approve all draft posts
            posts = db.query(CalendarPost).filter(
                CalendarPost.calendar_id == uuid.UUID(calendar_id),
                CalendarPost.status == "draft"
            ).all()

            for post in posts:
                post.status = "approved"

            content_calendar.status = "approved"
            content_calendar.approved_at = datetime.utcnow()
            content_calendar.approved_posts = len(posts)

            db.commit()

            logger.info(f"Approved calendar {calendar_id} with {len(posts)} posts")

            return {
                "success": True,
                "calendar_id": calendar_id,
                "approved_posts": len(posts),
            }

        except Exception as e:
            logger.error(f"Error approving calendar: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def update_post(
        self,
        db: Session,
        post_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a calendar post."""
        try:
            post = db.query(CalendarPost).filter(
                CalendarPost.id == uuid.UUID(post_id)
            ).first()

            if not post:
                return {
                    "success": False,
                    "error": "Post not found"
                }

            # Update fields
            if 'post_text' in updates:
                post.post_text = updates['post_text']
            if 'title' in updates:
                post.title = updates['title']
            if 'scheduled_date' in updates:
                post.scheduled_date = datetime.fromisoformat(updates['scheduled_date']).date()
            if 'scheduled_time' in updates:
                # Parse time string (format: HH:MM or HH:MM:SS)
                time_str = updates['scheduled_time']
                post.scheduled_time = datetime.strptime(time_str, '%H:%M:%S' if time_str.count(':') == 2 else '%H:%M').time()
            if 'platform' in updates:
                post.platform = updates['platform']
            if 'hashtags' in updates:
                post.hashtags = updates['hashtags']
            if 'status' in updates:
                post.status = updates['status']

            post.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Updated calendar post {post_id}")

            return {
                "success": True,
                "post": self._serialize_post(post),
            }

        except Exception as e:
            logger.error(f"Error updating post: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def delete_post(
        self,
        db: Session,
        post_id: str,
    ) -> Dict[str, Any]:
        """Delete a calendar post."""
        try:
            post = db.query(CalendarPost).filter(
                CalendarPost.id == uuid.UUID(post_id)
            ).first()

            if not post:
                return {
                    "success": False,
                    "error": "Post not found"
                }

            calendar_id = post.calendar_id
            db.delete(post)

            # Update calendar totals
            content_calendar = db.query(ContentCalendar).filter(
                ContentCalendar.id == calendar_id
            ).first()

            if content_calendar:
                content_calendar.total_posts = db.query(CalendarPost).filter(
                    CalendarPost.calendar_id == calendar_id
                ).count()

            db.commit()

            logger.info(f"Deleted calendar post {post_id}")

            return {
                "success": True,
                "post_id": post_id,
            }

        except Exception as e:
            logger.error(f"Error deleting post: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def delete_calendar(
        self,
        db: Session,
        tenant_id: str,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """Delete an entire calendar and all its posts."""
        try:
            content_calendar = db.query(ContentCalendar).filter(
                ContentCalendar.tenant_id == uuid.UUID(tenant_id),
                ContentCalendar.year == year,
                ContentCalendar.month == month,
            ).first()

            if not content_calendar:
                return {
                    "success": False,
                    "error": f"No calendar found for {year}-{month:02d}"
                }

            # Delete all posts in the calendar (CASCADE should handle this, but being explicit)
            db.query(CalendarPost).filter(
                CalendarPost.calendar_id == content_calendar.id
            ).delete()

            # Delete the calendar
            db.delete(content_calendar)
            db.commit()

            logger.info(f"Deleted calendar for {year}-{month:02d} (tenant {tenant_id})")

            return {
                "success": True,
                "message": f"Calendar for {year}-{month:02d} deleted successfully",
            }

        except Exception as e:
            logger.error(f"Error deleting calendar: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    def publish_calendar_post(
        self,
        db: Session,
        post_id: str,
    ) -> Dict[str, Any]:
        """
        Publish a calendar post to social media.

        Args:
            db: Database session
            post_id: Post UUID

        Returns:
            Dict with success status and results
        """
        try:
            post = db.query(CalendarPost).filter(
                CalendarPost.id == uuid.UUID(post_id)
            ).first()

            if not post:
                return {
                    "success": False,
                    "error": "Post not found"
                }

            if post.status != "approved":
                return {
                    "success": False,
                    "error": f"Post status is '{post.status}', must be 'approved' to publish"
                }

            # Get OAuth tokens
            platforms_to_post = []
            if post.platform == "both":
                platforms_to_post = ["facebook", "instagram"]
            else:
                platforms_to_post = [post.platform]

            results = []
            all_succeeded = True

            for platform in platforms_to_post:
                try:
                    # Get OAuth token
                    access_token = self.token_service.get_active_token(
                        db=db,
                        tenant_id=str(post.tenant_id),
                        platform=platform,
                    )

                    if not access_token:
                        raise Exception(f"No active OAuth token found for {platform}")

                    # Get social account
                    social_account = (
                        db.query(SocialAccount)
                        .filter(
                            SocialAccount.tenant_id == post.tenant_id,
                            SocialAccount.platform == platform,
                        )
                        .first()
                    )

                    if not social_account:
                        raise Exception(f"No social account found for {platform}")

                    # Build caption with hashtags
                    caption = post.post_text
                    if post.hashtags:
                        hashtags_str = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in post.hashtags])
                        caption = f"{caption}\n\n{hashtags_str}"

                    # Post to platform
                    if platform == "facebook":
                        platform_post_id = self._post_to_facebook(
                            page_id=social_account.platform_account_id,
                            access_token=access_token,
                            caption=caption,
                            image_url=post.image_url,
                        )
                        results.append({"platform": platform, "post_id": platform_post_id})
                    elif platform == "instagram":
                        if not post.image_url:
                            raise Exception("Instagram posts require an image")
                        platform_post_id = self._post_to_instagram(
                            instagram_account_id=social_account.platform_account_id,
                            access_token=access_token,
                            caption=caption,
                            image_url=post.image_url,
                        )
                        results.append({"platform": platform, "post_id": platform_post_id})

                except Exception as e:
                    all_succeeded = False
                    results.append({"platform": platform, "error": str(e)})
                    logger.error(f"Failed to post to {platform}: {e}")

            # Update post status
            if all_succeeded:
                post.status = "published"
                post.published_at = datetime.utcnow()
                # Store the first platform post ID (or combine them)
                if results:
                    post.platform_post_id = results[0].get("post_id")
            else:
                post.status = "failed"
                error_messages = [r.get("error") for r in results if "error" in r]
                post.error_message = "; ".join(error_messages)

            # Store engagement metrics placeholder
            post.engagement_metrics = {
                "published_to": [r.get("platform") for r in results if "post_id" in r],
                "published_at": datetime.utcnow().isoformat(),
            }

            db.commit()

            logger.info(f"Published calendar post {post_id} to {len([r for r in results if 'post_id' in r])} platform(s)")

            return {
                "success": all_succeeded,
                "post_id": post_id,
                "results": results,
                "status": post.status,
            }

        except Exception as e:
            logger.error(f"Error publishing calendar post: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    def _post_to_facebook(
        self,
        page_id: str,
        access_token: str,
        caption: str,
        image_url: str = None,
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
        image_url: str,
    ) -> str:
        """Post to Instagram and return media ID."""
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
