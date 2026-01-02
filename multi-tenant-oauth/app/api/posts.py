"""Posts API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
import requests

from app.models.base import get_db
from app.services import PostService, ContentGenerator, TokenService, ImageService, SchedulerService
from app.models import PostHistory, SocialAccount

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


# Pydantic models for request/response
class GenerateContentRequest(BaseModel):
    """Request model for content generation."""

    tenant_id: str = Field(..., description="Tenant UUID")
    restaurant_name: str = Field(..., description="Restaurant name")
    restaurant_description: str = Field(..., description="Brief restaurant description")
    post_type: str = Field("daily_special", description="Type of post")
    item_name: Optional[str] = Field(None, description="Featured item name")
    item_description: Optional[str] = Field(None, description="Item description")
    tone: str = Field("friendly", description="Tone of the post")
    platform: str = Field("facebook", description="Platform (facebook/instagram)")
    num_variations: int = Field(3, description="Number of variations to generate", ge=1, le=5)
    text_length: str = Field("extra_long", description="Text length preset (short/medium/long/extra_long)")


class CreatePostRequest(BaseModel):
    """Request model for creating a post."""

    tenant_id: str = Field(..., description="Tenant UUID")
    platform: str = Field(..., description="Platform (facebook/instagram)")
    caption: str = Field(..., description="Post caption/text")
    image_url: Optional[str] = Field(None, description="Image URL (direct URL)")
    asset_id: Optional[str] = Field(None, description="Brand asset ID (alternative to image_url)")
    campaign_name: Optional[str] = Field(None, description="Campaign name")
    item_name: Optional[str] = Field(None, description="Item name")
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled posting time")
    publish_now: bool = Field(True, description="Publish immediately")


class PostResponse(BaseModel):
    """Response model for post."""

    id: str
    tenant_id: str
    platform: str
    caption: str
    image_url: Optional[str]
    campaign_name: Optional[str]
    item_name: Optional[str]
    status: str
    posted_at: Optional[datetime]
    scheduled_for: Optional[datetime]
    platform_post_id: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PostStatsResponse(BaseModel):
    """Response model for post statistics."""

    total_posts: int
    published: int
    failed: int
    pending: int
    scheduled: int
    by_platform: dict
    days: int


class ContentVariationsResponse(BaseModel):
    """Response model for content variations."""

    variations: List[str]
    similarity_scores: List[float]


@router.post("/generate", response_model=ContentVariationsResponse)
async def generate_content(
    request: GenerateContentRequest,
    db: Session = Depends(get_db),
):
    """
    Generate AI-powered social media post variations.

    This endpoint generates multiple variations of a post caption using AI,
    and checks them against recent posts to avoid repetition.
    """
    post_service = PostService()
    content_generator = ContentGenerator()

    # Get recent captions to avoid similarity
    recent_captions = post_service.get_post_captions_for_similarity_check(
        db=db,
        tenant_id=request.tenant_id,
        platform=request.platform,
        days=30,
    )

    # Generate variations
    variations = []
    similarity_scores = []

    for i in range(request.num_variations):
        caption = content_generator.generate_post_caption(
            restaurant_name=request.restaurant_name,
            restaurant_description=request.restaurant_description,
            post_type=request.post_type,
            item_name=request.item_name,
            item_description=request.item_description,
            tone=request.tone,
            platform=request.platform,
            text_length=request.text_length,
            recent_captions=recent_captions if i == 0 else None,  # Only check first
        )

        # Check similarity
        similarity = content_generator.check_similarity(caption, recent_captions)

        variations.append(caption)
        similarity_scores.append(round(similarity, 2))

    return ContentVariationsResponse(
        variations=variations,
        similarity_scores=similarity_scores,
    )


@router.post("/create", response_model=PostResponse)
async def create_post(
    request: CreatePostRequest,
    db: Session = Depends(get_db),
):
    """
    Create and optionally publish a social media post.

    This endpoint creates a post record and optionally publishes it immediately
    to the specified platform using OAuth tokens.
    """
    post_service = PostService()
    token_service = TokenService()

    # Get social account
    social_account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.tenant_id == request.tenant_id,
            SocialAccount.platform == request.platform,
            SocialAccount.is_active == True,
        )
        .first()
    )

    if not social_account:
        raise HTTPException(
            status_code=404,
            detail=f"No active {request.platform} account found for tenant",
        )

    # Resolve asset_id to image_url if provided
    image_url = request.image_url
    if request.asset_id:
        from app.services import AssetService
        asset_service = AssetService()
        asset = asset_service.get_asset(db, request.asset_id)

        if not asset:
            raise HTTPException(
                status_code=404,
                detail="Asset not found",
            )

        # Use asset's file_url
        image_url = asset.file_url

        # Mark asset as used
        asset_service.mark_asset_used(db, request.asset_id)

    # Create post record
    post = post_service.create_post_record(
        db=db,
        tenant_id=request.tenant_id,
        social_account_id=str(social_account.id),
        platform=request.platform,
        caption=request.caption,
        image_url=image_url,
        campaign_name=request.campaign_name,
        item_name=request.item_name,
        scheduled_for=request.scheduled_for,
    )

    # Publish immediately if requested
    if request.publish_now and not request.scheduled_for:
        try:
            # Get OAuth token
            access_token = token_service.get_active_token(
                db=db,
                tenant_id=request.tenant_id,
                platform=request.platform,
            )

            if not access_token:
                raise HTTPException(
                    status_code=400,
                    detail="No active OAuth token found",
                )

            # Post to platform
            if request.platform == "facebook":
                platform_post_id = _post_to_facebook(
                    page_id=social_account.platform_account_id,
                    access_token=access_token,
                    caption=request.caption,
                    image_url=image_url,
                )
            elif request.platform == "instagram":
                platform_post_id = _post_to_instagram(
                    instagram_account_id=social_account.platform_account_id,
                    access_token=access_token,
                    caption=request.caption,
                    image_url=image_url,
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported platform: {request.platform}",
                )

            # Mark as published
            post = post_service.mark_post_published(
                db=db,
                post_id=str(post.id),
                platform_post_id=platform_post_id,
            )

        except Exception as e:
            # Mark as failed
            post = post_service.mark_post_failed(
                db=db,
                post_id=str(post.id),
                error_message=str(e),
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to publish post: {str(e)}",
            )

    return PostResponse(
        id=str(post.id),
        tenant_id=str(post.tenant_id),
        platform=post.platform,
        caption=post.caption,
        image_url=post.image_url,
        campaign_name=post.campaign_name,
        item_name=post.item_name,
        status=post.status,
        posted_at=post.posted_at,
        scheduled_for=post.scheduled_for,
        platform_post_id=post.platform_post_id,
        error_message=post.error_message,
        created_at=post.created_at,
    )


@router.get("/history", response_model=List[PostResponse])
async def get_post_history(
    tenant_id: str = Query(..., description="Tenant UUID"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    days: int = Query(30, description="Number of days to look back"),
    limit: int = Query(50, description="Maximum number of posts"),
    db: Session = Depends(get_db),
):
    """
    Get post history for a tenant.

    Returns a list of recent posts with their status and details.
    """
    post_service = PostService()

    posts = post_service.get_recent_posts(
        db=db,
        tenant_id=tenant_id,
        platform=platform,
        days=days,
        limit=limit,
    )

    return [
        PostResponse(
            id=str(post.id),
            tenant_id=str(post.tenant_id),
            platform=post.platform,
            caption=post.caption,
            image_url=post.image_url,
            campaign_name=post.campaign_name,
            item_name=post.item_name,
            status=post.status,
            posted_at=post.posted_at,
            scheduled_for=post.scheduled_for,
            platform_post_id=post.platform_post_id,
            error_message=post.error_message,
            created_at=post.created_at,
        )
        for post in posts
    ]


@router.get("/stats", response_model=PostStatsResponse)
async def get_post_stats(
    tenant_id: str = Query(..., description="Tenant UUID"),
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """
    Get posting statistics for a tenant.

    Returns summary statistics about posts over the specified time period.
    """
    post_service = PostService()

    stats = post_service.get_tenant_post_stats(
        db=db,
        tenant_id=tenant_id,
        days=days,
    )

    return PostStatsResponse(**stats)


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete (mark as deleted) a post.

    This marks the post as deleted in the history but doesn't remove it from the database.
    """
    post_service = PostService()

    success = post_service.delete_post(db=db, post_id=post_id)

    if not success:
        raise HTTPException(status_code=404, detail="Post not found")

    return {"message": "Post deleted successfully"}


# Helper functions for posting to platforms
def _post_to_facebook(
    page_id: str,
    access_token: str,
    caption: str,
    image_url: Optional[str] = None,
) -> str:
    """Post to Facebook and return post ID."""
    import os
    from pathlib import Path

    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"

    data = {
        "message": caption,
        "access_token": access_token,
    }

    files = None

    if image_url:
        # If there's an image, use the photos endpoint and upload file directly
        url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
        data["caption"] = caption
        del data["message"]

        # Extract file path from image_url
        # URL format: http://localhost:8000/uploads/images/{tenant_id}/{filename}
        # or: https://{ngrok}/uploads/images/{tenant_id}/{filename}
        if "/uploads/images/" in image_url:
            # Extract the relative path after /uploads/images/
            relative_path = image_url.split("/uploads/images/")[1]

            # Construct local file path (using absolute path from current directory)
            current_dir = Path.cwd()
            file_path = current_dir / "uploads" / "images" / relative_path

            if file_path.exists():
                # Read and upload file directly
                with open(file_path, "rb") as image_file:
                    files = {"source": image_file}
                    response = requests.post(url, data=data, files=files)
                    result = response.json()

                    if "id" in result:
                        return result["id"]
                    elif "error" in result:
                        raise Exception(result["error"].get("message", "Unknown error"))
                    else:
                        raise Exception("Failed to post to Facebook")
            else:
                raise Exception(f"Image file not found at: {file_path}")
        else:
            raise Exception(f"Invalid image URL format: {image_url}")

    # Post without image
    response = requests.post(url, data=data)
    result = response.json()

    if "id" in result:
        return result["id"]
    elif "error" in result:
        raise Exception(result["error"].get("message", "Unknown error"))
    else:
        raise Exception("Failed to post to Facebook")


def _post_to_instagram(
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
        raise Exception(error.get("message", "Failed to create Instagram container"))

    container_id = result["id"]

    # Step 2: Publish container
    publish_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media_publish"
    publish_data = {
        "creation_id": container_id,
        "access_token": access_token,
    }

    response = requests.post(publish_url, data=publish_data)
    result = response.json()

    if "id" in result:
        return result["id"]
    elif "error" in result:
        raise Exception(result["error"].get("message", "Failed to publish Instagram post"))
    else:
        raise Exception("Failed to publish to Instagram")


# New endpoints for image upload, scheduling, and Instagram

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    tenant_id: str = Query(..., description="Tenant UUID"),
):
    """
    Upload an image for a post.

    Returns the image URL that can be used when creating posts.
    """
    try:
        image_service = ImageService()
        file_path, file_url = await image_service.upload_image(file, tenant_id)

        return {
            "file_path": file_path,
            "file_url": file_url,
            "filename": file.filename,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/schedule", response_model=PostResponse)
async def schedule_post(
    request: CreatePostRequest,
    db: Session = Depends(get_db),
):
    """
    Schedule a post for future publication.

    Same as create endpoint but requires scheduled_for datetime.
    """
    if not request.scheduled_for:
        raise HTTPException(
            status_code=400,
            detail="scheduled_for is required for scheduling posts",
        )

    scheduler_service = SchedulerService()

    # Get social account
    social_account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.tenant_id == request.tenant_id,
            SocialAccount.platform == request.platform,
            SocialAccount.is_active == True,
        )
        .first()
    )

    if not social_account:
        raise HTTPException(
            status_code=404,
            detail=f"No active {request.platform} account found for tenant",
        )

    # Schedule the post
    post = scheduler_service.schedule_post(
        db=db,
        tenant_id=request.tenant_id,
        social_account_id=str(social_account.id),
        platform=request.platform,
        caption=request.caption,
        image_url=request.image_url,
        scheduled_for=request.scheduled_for,
        campaign_name=request.campaign_name,
        item_name=request.item_name,
    )

    return PostResponse(
        id=str(post.id),
        tenant_id=str(post.tenant_id),
        platform=post.platform,
        caption=post.caption,
        image_url=post.image_url,
        campaign_name=post.campaign_name,
        item_name=post.item_name,
        status=post.status,
        posted_at=post.posted_at,
        scheduled_for=post.scheduled_for,
        platform_post_id=post.platform_post_id,
        error_message=post.error_message,
        created_at=post.created_at,
    )


@router.get("/scheduled", response_model=List[PostResponse])
async def get_scheduled_posts(
    tenant_id: str = Query(..., description="Tenant UUID"),
    db: Session = Depends(get_db),
):
    """Get all scheduled posts for a tenant."""
    posts = (
        db.query(PostHistory)
        .filter(
            PostHistory.tenant_id == tenant_id,
            PostHistory.status == "scheduled",
        )
        .order_by(PostHistory.scheduled_for)
        .all()
    )

    return [
        PostResponse(
            id=str(post.id),
            tenant_id=str(post.tenant_id),
            platform=post.platform,
            caption=post.caption,
            image_url=post.image_url,
            campaign_name=post.campaign_name,
            item_name=post.item_name,
            status=post.status,
            posted_at=post.posted_at,
            scheduled_for=post.scheduled_for,
            platform_post_id=post.platform_post_id,
            error_message=post.error_message,
            created_at=post.created_at,
        )
        for post in posts
    ]


@router.post("/{post_id}/publish")
async def publish_scheduled_post(
    post_id: str,
    db: Session = Depends(get_db),
):
    """Publish a scheduled post immediately."""
    scheduler_service = SchedulerService()

    success = scheduler_service.publish_post(db, post_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to publish post. Post may not exist or not be in scheduled status.",
        )

    return {"message": "Post published successfully"}


@router.delete("/{post_id}/cancel")
async def cancel_scheduled_post(
    post_id: str,
    db: Session = Depends(get_db),
):
    """Cancel a scheduled post."""
    scheduler_service = SchedulerService()

    success = scheduler_service.cancel_scheduled_post(db, post_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to cancel post. Post may not exist or not be in scheduled status.",
        )

    return {"message": "Scheduled post cancelled successfully"}


# Analytics endpoints

@router.get("/analytics")
async def get_analytics(
    tenant_id: str = Query(..., description="Tenant UUID"),
    days: int = Query(30, description="Number of days to analyze"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    db: Session = Depends(get_db),
):
    """Get comprehensive analytics for a tenant."""
    from app.services.analytics_service import AnalyticsService
    
    analytics_service = AnalyticsService()
    analytics = analytics_service.get_post_analytics(
        db=db,
        tenant_id=tenant_id,
        days=days,
        platform=platform,
    )
    
    return analytics


@router.get("/analytics/timeseries")
async def get_time_series(
    tenant_id: str = Query(..., description="Tenant UUID"),
    days: int = Query(30, description="Number of days"),
    db: Session = Depends(get_db),
):
    """Get time series data for charts."""
    from app.services.analytics_service import AnalyticsService
    
    analytics_service = AnalyticsService()
    data = analytics_service.get_time_series_data(
        db=db,
        tenant_id=tenant_id,
        days=days,
    )
    
    return {"data": data}


@router.get("/analytics/top-posts")
async def get_top_posts(
    tenant_id: str = Query(..., description="Tenant UUID"),
    limit: int = Query(10, description="Number of top posts"),
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """Get top performing posts."""
    from app.services.analytics_service import AnalyticsService
    
    analytics_service = AnalyticsService()
    top_posts = analytics_service.get_top_posts(
        db=db,
        tenant_id=tenant_id,
        limit=limit,
        days=days,
    )
    
    return {"top_posts": top_posts}


@router.post("/{post_id}/fetch-insights")
async def fetch_post_insights(
    post_id: str,
    db: Session = Depends(get_db),
):
    """Fetch latest engagement metrics from Facebook/Instagram for a post."""
    from app.services.analytics_service import AnalyticsService
    
    analytics_service = AnalyticsService()
    
    # Get post to determine platform
    post = db.query(PostHistory).filter(PostHistory.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.platform == "facebook":
        metrics = analytics_service.fetch_facebook_insights(db, post_id)
    elif post.platform == "instagram":
        metrics = analytics_service.fetch_instagram_insights(db, post_id)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {post.platform}")
    
    if not metrics:
        raise HTTPException(status_code=400, detail="Failed to fetch insights")
    
    return {"metrics": metrics}
