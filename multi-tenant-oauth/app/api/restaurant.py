"""Restaurant configuration and data import API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import os
import tempfile
from datetime import datetime

from app.models.base import get_db
from app.models import RestaurantProfile, MenuItem, SalesData, Tenant
from app.services import MenuImportService, SalesImportService
from app.services.restaurant_intelligence_service import RestaurantIntelligenceService
from app.services.post_suggestion_service import PostSuggestionService
from app.services.content_calendar_service import ContentCalendarService
from app.services.asset_service import AssetService
from app.services.folder_service import FolderService
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/restaurant", tags=["restaurant"])
logger = get_logger(__name__)


# Response Models
class RestaurantProfileResponse(BaseModel):
    """Restaurant profile response."""

    id: str
    tenant_id: str
    name: Optional[str]
    cuisine_type: Optional[str]
    location: Optional[Dict[str, Any]]
    website: Optional[str]
    phone: Optional[str]
    brand_analysis: Optional[Dict[str, Any]]
    sales_insights: Optional[Dict[str, Any]]
    content_strategy: Optional[Dict[str, Any]]
    last_menu_import: Optional[datetime]
    last_sales_import: Optional[datetime]
    menu_items_count: int
    sales_records_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuItemResponse(BaseModel):
    """Menu item response."""

    id: str
    tenant_id: str
    external_id: Optional[str]
    category: Optional[str]
    name: str
    description: Optional[str]
    image_url: Optional[str]
    price: Optional[float]
    cost: Optional[float]
    has_modifiers: bool
    modifiers: Optional[List[Dict[str, Any]]]
    is_deal: bool
    out_of_stock: bool
    times_ordered: int
    total_revenue: Optional[float]
    popularity_rank: Optional[int]
    times_posted_about: int
    last_featured_date: Optional[datetime]

    class Config:
        from_attributes = True


class ImportResponse(BaseModel):
    """Data import response."""

    success: bool
    items_imported: Optional[int] = None
    orders_imported: Optional[int] = None
    statistics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AnalysisResponse(BaseModel):
    """AI analysis response."""

    success: bool
    brand_analysis: Optional[Dict[str, Any]] = None
    sales_insights: Optional[Dict[str, Any]] = None
    content_strategy: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    """Request model for updating restaurant profile."""

    name: Optional[str] = None
    cuisine_type: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    website: Optional[str] = None
    phone: Optional[str] = None


class PostSuggestionResponse(BaseModel):
    """Post suggestion response."""

    success: bool
    suggestions: Optional[List[Dict[str, Any]]] = None
    generated_at: Optional[str] = None
    error: Optional[str] = None


class SyncMenuAssetsResponse(BaseModel):
    """Menu assets sync response."""

    success: bool
    total_items: int
    synced_count: int
    skipped_count: int
    error: Optional[str] = None


# Endpoints
@router.post("/{tenant_id}/import/menu", response_model=ImportResponse)
async def import_menu_data(
    tenant_id: str,
    file: UploadFile = File(..., description="Innowi POS menu Excel file"),
    db: Session = Depends(get_db),
):
    """
    Import menu data from Innowi POS Excel file.

    Args:
        tenant_id: Tenant UUID
        file: Excel file with menu data
        db: Database session

    Returns:
        Import statistics

    Raises:
        HTTPException: If tenant not found or import fails
    """
    logger.info(f"Importing menu data for tenant {tenant_id}")

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")

    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Import menu data
        menu_service = MenuImportService()
        result = await menu_service.import_menu_from_excel(
            db=db,
            file_path=tmp_file_path,
            tenant_id=tenant_id,
        )

        # Clean up temp file
        os.unlink(tmp_file_path)

        logger.info(f"Menu import completed for tenant {tenant_id}: {result.get('items_imported', 0)} items")

        return ImportResponse(**result)

    except Exception as e:
        logger.error(f"Error importing menu data: {e}")
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tenant_id}/import/sales", response_model=ImportResponse)
async def import_sales_data(
    tenant_id: str,
    file: UploadFile = File(..., description="Innowi POS order history Excel file"),
    db: Session = Depends(get_db),
):
    """
    Import sales/order history from Innowi POS Excel file.

    Args:
        tenant_id: Tenant UUID
        file: Excel file with order history
        db: Database session

    Returns:
        Import statistics

    Raises:
        HTTPException: If tenant not found or import fails
    """
    logger.info(f"Importing sales data for tenant {tenant_id}")

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")

    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Import sales data
        sales_service = SalesImportService()
        result = await sales_service.import_sales_from_excel(
            db=db,
            file_path=tmp_file_path,
            tenant_id=tenant_id,
        )

        # Clean up temp file
        os.unlink(tmp_file_path)

        logger.info(f"Sales import completed for tenant {tenant_id}: {result.get('orders_imported', 0)} orders")

        return ImportResponse(**result)

    except Exception as e:
        logger.error(f"Error importing sales data: {e}")
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tenant_id}/analyze", response_model=AnalysisResponse)
async def analyze_restaurant(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Trigger AI analysis of restaurant menu and sales data.

    This endpoint uses GPT-4 to:
    1. Analyze menu items and generate brand personality
    2. Analyze sales trends and identify opportunities
    3. Generate content strategy recommendations

    Args:
        tenant_id: Tenant UUID
        db: Database session

    Returns:
        Analysis results with brand personality, sales insights, and content strategy

    Raises:
        HTTPException: If tenant not found or analysis fails
    """
    logger.info(f"Starting AI analysis for tenant {tenant_id}")

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Run AI analysis
    try:
        intelligence_service = RestaurantIntelligenceService()
        result = await intelligence_service.analyze_restaurant(
            db=db,
            tenant_id=tenant_id,
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Analysis failed'))

        logger.info(f"AI analysis completed for tenant {tenant_id}")

        return AnalysisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing restaurant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tenant_id}/suggestions", response_model=PostSuggestionResponse)
async def get_post_suggestions(
    tenant_id: str,
    count: int = Query(5, ge=1, le=10, description="Number of suggestions to generate"),
    text_length: str = Query("extra_long", description="Text length preset: short, medium, long, extra_long"),
    db: Session = Depends(get_db),
):
    """
    Generate intelligent post suggestions based on restaurant context.

    This endpoint analyzes:
    - Restaurant profile and brand personality
    - Sales trends and patterns
    - Menu items and popularity
    - Content strategy recommendations

    And generates context-aware post suggestions including:
    - Promotional posts for slow days
    - Product showcases for bestsellers
    - Weekend traffic drivers
    - Engagement posts
    - Customer appreciation posts

    Args:
        tenant_id: Tenant UUID
        count: Number of suggestions to generate (1-10)
        db: Database session

    Returns:
        List of post suggestions with text, timing, and reasoning

    Raises:
        HTTPException: If tenant not found or suggestion generation fails
    """
    logger.info(f"Generating {count} post suggestions for tenant {tenant_id}")

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Generate suggestions
    try:
        suggestion_service = PostSuggestionService()
        result = await suggestion_service.generate_suggestions(
            db=db,
            tenant_id=tenant_id,
            count=count,
            text_length=text_length,
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Suggestion generation failed'))

        logger.info(f"Generated {len(result.get('suggestions', []))} suggestions for tenant {tenant_id}")

        return PostSuggestionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}/profile", response_model=RestaurantProfileResponse)
def get_restaurant_profile(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Get restaurant profile with AI analysis and import metadata.

    Args:
        tenant_id: Tenant UUID
        db: Database session

    Returns:
        Restaurant profile

    Raises:
        HTTPException: If tenant or profile not found
    """
    logger.info(f"Fetching restaurant profile for tenant {tenant_id}")

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get or create profile
    profile = db.query(RestaurantProfile).filter(
        RestaurantProfile.tenant_id == uuid.UUID(tenant_id)
    ).first()

    if not profile:
        # Create empty profile
        profile = RestaurantProfile(
            tenant_id=uuid.UUID(tenant_id),
            menu_items_count=0,
            sales_records_count=0,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return RestaurantProfileResponse(
        id=str(profile.id),
        tenant_id=str(profile.tenant_id),
        name=profile.name,
        cuisine_type=profile.cuisine_type,
        location=profile.location,
        website=profile.website,
        phone=profile.phone,
        brand_analysis=profile.brand_analysis,
        sales_insights=profile.sales_insights,
        content_strategy=profile.content_strategy,
        last_menu_import=profile.last_menu_import,
        last_sales_import=profile.last_sales_import,
        menu_items_count=profile.menu_items_count,
        sales_records_count=profile.sales_records_count,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.put("/{tenant_id}/profile", response_model=RestaurantProfileResponse)
def update_restaurant_profile(
    tenant_id: str,
    update_data: UpdateProfileRequest,
    db: Session = Depends(get_db),
):
    """
    Update restaurant profile information.

    Args:
        tenant_id: Tenant UUID
        update_data: Profile update data
        db: Database session

    Returns:
        Updated restaurant profile

    Raises:
        HTTPException: If tenant or profile not found
    """
    logger.info(f"Updating restaurant profile for tenant {tenant_id}")

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get or create profile
    profile = db.query(RestaurantProfile).filter(
        RestaurantProfile.tenant_id == uuid.UUID(tenant_id)
    ).first()

    if not profile:
        # Create new profile with provided data
        profile = RestaurantProfile(
            tenant_id=uuid.UUID(tenant_id),
            name=update_data.name,
            cuisine_type=update_data.cuisine_type,
            location=update_data.location,
            website=update_data.website,
            phone=update_data.phone,
            menu_items_count=0,
            sales_records_count=0,
        )
        db.add(profile)
    else:
        # Update existing profile (only update fields that are provided)
        if update_data.name is not None:
            profile.name = update_data.name
        if update_data.cuisine_type is not None:
            profile.cuisine_type = update_data.cuisine_type
        if update_data.location is not None:
            profile.location = update_data.location
        if update_data.website is not None:
            profile.website = update_data.website
        if update_data.phone is not None:
            profile.phone = update_data.phone

    db.commit()
    db.refresh(profile)

    logger.info(f"Restaurant profile updated for tenant {tenant_id}")

    return RestaurantProfileResponse(
        id=str(profile.id),
        tenant_id=str(profile.tenant_id),
        name=profile.name,
        cuisine_type=profile.cuisine_type,
        location=profile.location,
        website=profile.website,
        phone=profile.phone,
        brand_analysis=profile.brand_analysis,
        sales_insights=profile.sales_insights,
        content_strategy=profile.content_strategy,
        last_menu_import=profile.last_menu_import,
        last_sales_import=profile.last_sales_import,
        menu_items_count=profile.menu_items_count,
        sales_records_count=profile.sales_records_count,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/{tenant_id}/menu", response_model=List[MenuItemResponse])
def get_menu_items(
    tenant_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    sort_by: str = Query("popularity_rank", description="Sort field: popularity_rank, name, price"),
    db: Session = Depends(get_db),
):
    """
    Get menu items for a restaurant.

    Args:
        tenant_id: Tenant UUID
        category: Optional category filter
        limit: Maximum items to return
        offset: Items to skip
        sort_by: Sort field
        db: Database session

    Returns:
        List of menu items

    Raises:
        HTTPException: If tenant not found
    """
    logger.info(f"Fetching menu items for tenant {tenant_id}")

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Build query
    query = db.query(MenuItem).filter(MenuItem.tenant_id == uuid.UUID(tenant_id))

    # Apply filters
    if category:
        query = query.filter(MenuItem.category == category)

    # Apply sorting
    if sort_by == "popularity_rank":
        query = query.filter(MenuItem.popularity_rank.isnot(None)).order_by(MenuItem.popularity_rank)
    elif sort_by == "name":
        query = query.order_by(MenuItem.name)
    elif sort_by == "price":
        query = query.order_by(MenuItem.price.desc())

    # Apply pagination
    items = query.limit(limit).offset(offset).all()

    return [
        MenuItemResponse(
            id=str(item.id),
            tenant_id=str(item.tenant_id),
            external_id=item.external_id,
            category=item.category,
            name=item.name,
            description=item.description,
            image_url=item.image_url,
            price=float(item.price) if item.price else None,
            cost=float(item.cost) if item.cost else None,
            has_modifiers=item.has_modifiers,
            modifiers=item.modifiers,
            is_deal=item.is_deal,
            out_of_stock=item.out_of_stock,
            times_ordered=item.times_ordered,
            total_revenue=float(item.total_revenue) if item.total_revenue else None,
            popularity_rank=item.popularity_rank,
            times_posted_about=item.times_posted_about,
            last_featured_date=item.last_featured_date,
        )
        for item in items
    ]


@router.get("/{tenant_id}/menu/categories")
def get_menu_categories(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Get list of menu categories for a restaurant.

    Args:
        tenant_id: Tenant UUID
        db: Database session

    Returns:
        List of category names with item counts

    Raises:
        HTTPException: If tenant not found
    """
    logger.info(f"Fetching menu categories for tenant {tenant_id}")

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get categories with counts
    from sqlalchemy import func

    categories = (
        db.query(MenuItem.category, func.count(MenuItem.id).label('count'))
        .filter(MenuItem.tenant_id == uuid.UUID(tenant_id))
        .filter(MenuItem.category.isnot(None))
        .group_by(MenuItem.category)
        .order_by(MenuItem.category)
        .all()
    )

    return [
        {"category": cat, "item_count": count}
        for cat, count in categories
    ]


# ============================================================================
# CONTENT CALENDAR ENDPOINTS
# ============================================================================

class GenerateCalendarRequest(BaseModel):
    """Request to generate monthly calendar."""
    year: int
    month: int  # 1-12
    posts_count: Optional[int] = 25


class CreatePostRequest(BaseModel):
    """Request to create calendar post."""
    calendar_id: str
    title: str
    post_text: str
    scheduled_date: str
    scheduled_time: str
    platform: str = "both"
    post_type: str = "general"
    status: str = "draft"
    hashtags: Optional[List[str]] = None
    image_url: Optional[str] = None


class UpdatePostRequest(BaseModel):
    """Request to update calendar post."""
    post_text: Optional[str] = None
    title: Optional[str] = None
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    platform: Optional[str] = None
    hashtags: Optional[List[str]] = None
    status: Optional[str] = None


@router.post("/{tenant_id}/calendar/generate")
async def generate_monthly_calendar(
    tenant_id: str,
    request: GenerateCalendarRequest,
    db: Session = Depends(get_db)
):
    """Generate a monthly content calendar with strategically distributed posts."""
    calendar_service = ContentCalendarService()
    result = await calendar_service.generate_monthly_calendar(
        db,
        tenant_id,
        request.year,
        request.month,
        request.posts_count
    )

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.get("/{tenant_id}/calendar/current")
async def get_current_calendar(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Get or create calendar for the current month."""
    from datetime import datetime
    from app.models import ContentCalendar

    # Get current year and month
    now = datetime.now()
    year = now.year
    month = now.month

    # Try to find existing calendar for current month
    calendar = (
        db.query(ContentCalendar)
        .filter(
            ContentCalendar.tenant_id == uuid.UUID(tenant_id),
            ContentCalendar.year == year,
            ContentCalendar.month == month
        )
        .first()
    )

    # If calendar doesn't exist, create it
    if not calendar:
        calendar = ContentCalendar(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            year=year,
            month=month,
            total_posts=0,
            status='draft'
        )
        db.add(calendar)
        db.commit()
        db.refresh(calendar)

    return {
        "id": str(calendar.id),
        "tenant_id": str(calendar.tenant_id),
        "year": calendar.year,
        "month": calendar.month,
        "total_posts": calendar.total_posts,
        "status": calendar.status
    }


@router.get("/{tenant_id}/calendar/{year}/{month}")
async def get_calendar(
    tenant_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """Get content calendar for a specific month."""
    calendar_service = ContentCalendarService()
    result = await calendar_service.get_calendar(db, tenant_id, year, month)

    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))

    return result


@router.put("/{tenant_id}/calendar/{calendar_id}/approve")
async def approve_calendar(
    tenant_id: str,
    calendar_id: str,
    db: Session = Depends(get_db)
):
    """Approve all posts in a calendar."""
    calendar_service = ContentCalendarService()
    result = await calendar_service.approve_calendar(db, calendar_id)

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.post("/{tenant_id}/calendar/post")
async def create_calendar_post(
    tenant_id: str,
    request: CreatePostRequest,
    db: Session = Depends(get_db)
):
    """Create a new calendar post."""
    import uuid
    from datetime import datetime
    from app.models import CalendarPost

    try:
        # Parse date and time
        scheduled_date = datetime.fromisoformat(request.scheduled_date).date()
        # Parse time in HH:MM format
        scheduled_time = datetime.strptime(request.scheduled_time, "%H:%M").time()

        # Create calendar post
        calendar_post = CalendarPost(
            id=uuid.uuid4(),
            calendar_id=uuid.UUID(request.calendar_id),
            tenant_id=uuid.UUID(tenant_id),
            post_type=request.post_type,
            title=request.title,
            post_text=request.post_text,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            platform=request.platform,
            status=request.status,
            hashtags=request.hashtags or [],
            image_url=request.image_url,
            generated_by='manual',
        )

        db.add(calendar_post)
        db.commit()
        db.refresh(calendar_post)

        return {
            "success": True,
            "post_id": str(calendar_post.id),
            "message": "Post created successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create post: {str(e)}")


@router.put("/{tenant_id}/calendar/post/{post_id}")
async def update_calendar_post(
    tenant_id: str,
    post_id: str,
    request: UpdatePostRequest,
    db: Session = Depends(get_db)
):
    """Update a calendar post."""
    calendar_service = ContentCalendarService()
    updates = request.dict(exclude_unset=True)
    result = await calendar_service.update_post(db, post_id, updates)

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.delete("/{tenant_id}/calendar/post/{post_id}")
async def delete_calendar_post(
    tenant_id: str,
    post_id: str,
    db: Session = Depends(get_db)
):
    """Delete a calendar post."""
    calendar_service = ContentCalendarService()
    result = await calendar_service.delete_post(db, post_id)

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.delete("/{tenant_id}/calendar/{year}/{month}")
async def delete_calendar(
    tenant_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """Delete an entire calendar and all its posts."""
    calendar_service = ContentCalendarService()
    result = await calendar_service.delete_calendar(db, tenant_id, year, month)

    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))

    return result


@router.post("/{tenant_id}/sync-menu-assets", response_model=SyncMenuAssetsResponse)
async def sync_menu_assets(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Sync menu item images to brand asset library.

    Downloads images from menu items and creates organized brand assets
    in category-based folders (Dishes/Pizza, Dishes/Pasta, etc.).

    Args:
        tenant_id: Tenant UUID
        db: Database session

    Returns:
        Sync statistics (total items, synced count, skipped count)

    Raises:
        HTTPException: If tenant not found
    """
    logger.info(f"Starting menu assets sync for tenant {tenant_id}")

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get all menu items with image URLs
    menu_items = (
        db.query(MenuItem)
        .filter(MenuItem.tenant_id == uuid.UUID(tenant_id))
        .filter(MenuItem.image_url != None)
        .filter(MenuItem.image_url != "")
        .all()
    )

    if not menu_items:
        logger.info(f"No menu items with images found for tenant {tenant_id}")
        return SyncMenuAssetsResponse(
            success=True,
            total_items=0,
            synced_count=0,
            skipped_count=0,
        )

    # Initialize services
    asset_service = AssetService()
    folder_service = FolderService()

    synced_count = 0
    skipped_count = 0

    # Process each menu item
    for item in menu_items:
        try:
            # Skip if already has asset
            if item.asset_id:
                logger.debug(f"Menu item {item.name} already has asset, skipping")
                skipped_count += 1
                continue

            # Skip if no valid category
            if not item.category:
                logger.debug(f"Menu item {item.name} has no category, skipping")
                skipped_count += 1
                continue

            # Get or create category folder (e.g., Dishes/Pizza)
            category_folder = folder_service.get_or_create_category_folder(
                db=db,
                tenant_id=tenant_id,
                category_name=item.category,
            )

            # Download image and create asset
            asset = await asset_service.create_asset_from_url(
                db=db,
                url=item.image_url,
                tenant_id=tenant_id,
                folder_id=str(category_folder.id),
                title=item.name,
                description=item.description or f"{item.category} - {item.name}",
                tags=[item.category, "menu-item"],
            )

            if asset:
                # Link asset to menu item
                item.asset_id = asset.id
                db.commit()
                synced_count += 1
                logger.debug(f"Successfully synced asset for {item.name}")
            else:
                # Download failed (silently skip)
                skipped_count += 1
                logger.debug(f"Failed to download image for {item.name}, skipping")

        except Exception as e:
            # Skip on any error (per user preference: skip failed images silently)
            logger.warning(f"Error syncing asset for {item.name}: {str(e)}")
            skipped_count += 1
            continue

    logger.info(
        f"Menu assets sync completed for tenant {tenant_id}: "
        f"{synced_count} synced, {skipped_count} skipped out of {len(menu_items)} total"
    )

    return SyncMenuAssetsResponse(
        success=True,
        total_items=len(menu_items),
        synced_count=synced_count,
        skipped_count=skipped_count,
    )
