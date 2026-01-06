# Changelog

All notable changes to the Social Automation Multi-Tenant OAuth Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Restaurant description configuration per tenant (currently hardcoded)
- Multi-account posting (post to multiple Facebook/Instagram accounts simultaneously)
- Advanced analytics dashboard with engagement tracking
- Multi-image carousel posts
- Video posting support
- Post templates library
- Team collaboration features
- Webhook integration for real-time updates
- Automated publishing to approved calendar posts

---

## [2.4.0] - 2026-01-06

### 🎉 Major Achievement: Instagram Posting Fully Working!

### Added
- **Instagram Posting with S3 URLs**
  - Full Instagram posting support using menu item images from S3
  - Business Manager API integration for fetching Instagram Business accounts
  - Automatic detection and connection of Instagram accounts linked to Facebook Pages
  - Two-step Instagram publishing: container creation → publish
  - Complete error handling with detailed logging
  - Support for captions, hashtags, and image posts

- **S3 URL Priority System**
  - Updated `post_suggestion_service.py` to prioritize direct S3 URLs over asset_id lookups
  - Modified `posts.py` API to only use asset_id when no direct URL is provided
  - Added defensive URL resolution in `content_calendar_service.py`
  - Smart image selection that prevents ngrok URL usage

- **Database Migration for S3 URLs**
  - Migrated 49 brand assets from ngrok URLs to S3 URLs
  - Synchronized brand_assets.file_url with menu_items.image_url for all menu items
  - Maintained data integrity between menu items and brand assets

- **Frontend S3 URL Support**
  - Fixed `getRelativeImagePath()` to preserve full S3 URLs
  - Asset library now displays images from both S3 and local storage
  - Proper handling of external URLs (S3) vs internal paths (ngrok)
  - Image preview and selection working with S3 URLs

### Fixed
- **Instagram Image Download Error (Error 9004, subcode 2207052)**
  - Root cause: System was using ngrok URLs that Instagram couldn't access
  - Solution: Prioritize S3 URLs from menu items over brand_assets references
  - Result: Instagram can now successfully download images from public S3 URLs

- **Asset Library Image Loading**
  - Fixed 404 errors when displaying S3-hosted images
  - Corrected URL construction in frontend JavaScript
  - Browser now loads images directly from S3 instead of proxying through ngrok

- **Token Permissions Error**
  - Fixed permissions error by passing platform_account_id to token retrieval
  - Ensures correct page-specific token is used for each social account

### Technical Details
- Business Manager API queries both `/me/accounts` and `/me/businesses` endpoints
- Handles pages in personal profiles and business portfolios
- Deduplication logic prevents duplicate page entries
- OAuth scopes: `business_management`, `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`

### Documentation
- Updated INSTAGRAM_SETUP.md with complete working status
- Documented S3 URL solution and migration process
- Added troubleshooting guide for image hosting

---

## [2.2.0] - 2026-01-02

### Added
- **Social Account Management UI in Restaurant Config**
  - Connected accounts section showing all linked Facebook/Instagram pages
  - Account status badges with token expiration monitoring
  - Connect/Reconnect/Disconnect functionality with confirmation dialogs
  - Visual account cards displaying platform, name, connection date, and health status
  - Empty state UI for when no accounts are connected
  - OAuth callback handler for seamless post-authentication flow

- **Auto-Populate Post Fields from Image Metadata**
  - Image selection moved to top of Create Post form for better UX
  - Automatic population of "Item Name" from asset title metadata
  - Automatic population of "Description" from asset description metadata
  - Visual feedback (green border flash) when fields are auto-filled
  - Smart behavior: only fills empty fields, preserves user-entered data
  - Works with both "Browse Asset Library" and "Quick Upload" methods
  - Helpful tip text guiding users to select image first

### Fixed
- **OAuth Redirect URI Configuration**
  - Updated redirect URIs to support ngrok for development
  - Fixed "Can't load URL" error from Facebook OAuth
  - Changed API_URL from hardcoded localhost to dynamic `window.location.origin`
  - Now works seamlessly with both localhost and ngrok domains
  - Fixed CORS issues when accessing via public URLs

### Changed
- Create Post form field order optimized for better workflow
- Image selection buttons enhanced with emoji icons (📁 📤)
- Restaurant config page now shows connected social accounts prominently

### Technical
- Enhanced `showSelectedImage()` function with metadata extraction
- Added account management JavaScript functions for OAuth flow
- Improved form UX with visual feedback on auto-population
- Dynamic API URL detection for multi-domain support

---

## [2.1.1] - 2026-01-02

### Fixed
- **Calendar Scheduling Logic - Hybrid Day-of-Week Distribution**
  - Fixed posts clustering on same days of the week (previously all on Sunday/Wednesday)
  - Implemented hybrid scheduling algorithm that respects `target_day` from post suggestions
  - Weekend traffic posts now actually post on Fridays (not Wednesdays)
  - Engagement posts now land on Wednesdays (not random Sundays)
  - Customer appreciation posts now schedule on Thursdays (not Wednesdays)
  - Product showcase posts distribute across Tuesdays throughout the month

### Changed
- **Smart Day Distribution Algorithm**
  - Posts now scheduled based on marketing strategy (day-of-week) instead of mathematical distribution (day-of-month)
  - When multiple posts want the same day, they spread across different weeks
  - Falls back to adjacent days if preferred day is full
  - Single posts land on middle occurrence of target day for better distribution
  - Maintains chronological order within the month

### Technical Details
- Added `_smart_day_distribution()` method to ContentCalendarService
- Groups suggestions by `target_day` field
- Builds map of day names to day numbers for the month
- Distributes posts evenly across available occurrences of target days
- Replaced mathematical `_calculate_posting_schedule()` with strategic scheduling
- Modified `_generate_calendar_posts()` to use new hybrid algorithm

### Example Improvement
**Before (v2.1.0):** 8 posts → Days 1, 4, 8, 11, 15, 18, 22, 25 (all Sunday/Wednesday)
**After (v2.1.1):** 8 posts → Thu 1st, Tue 6th, Tue 13th, Fri 16th, Wed 21st, Thu 22nd, Tue 27th, Thu 29th (strategic days)

### Benefits
- ✅ Posts appear on strategically optimal days of the week
- ✅ Weekend traffic posts actually drive Friday→Saturday traffic
- ✅ Engagement posts hit mid-week engagement peaks
- ✅ Better distribution across the week (not clustered on 2 days)
- ✅ Respects marketing strategy from AI analysis

---

## [2.1.0] - 2026-01-02

### Added
- **Content Calendar Generation Improvements**
  - Added `use_ai_for_all_posts` configuration field to RestaurantProfile model
  - New UI toggle in Restaurant Config: "🤖 Use AI for All Posts"
  - API endpoint: `POST /api/v1/restaurant/{tenant_id}/settings/toggle-ai-for-all`
  - Complete OpenAI request/response logging for transparency and debugging
  - Real-time progress tracking during calendar generation with detailed logs

### Changed
- **Calendar Post Count**: Default changed from 25 to 8 posts (recommended: 8-15)
- **Post Generation Logic**: Now generates exactly the requested number of posts
  - Loops through post strategies until reaching target count
  - Adds variety with random menu items and promotional variations
  - Maximum 10 cycles to prevent infinite loops
- **AI Content Generation**: Engagement and customer appreciation posts now support AI mode
  - When `use_ai_for_all_posts = True`: All posts use OpenAI GPT-4
  - When `use_ai_for_all_posts = False` (default): Mixed mode uses templates for some posts
  - Mixed mode saves costs while maintaining quality for key promotional posts

### Fixed
- **Post Count Mismatch**: Calendar generation now respects requested post count
  - Previously only generated up to 6 posts regardless of request
  - Now generates 8, 15, 25, or any requested count (5-31 range)

### Technical Details
- Database migration: `20260101_2222_1cc5db06fca8_add_use_ai_for_all_posts_to_restaurant_`
- Modified files:
  - `app/models/restaurant_profile.py` - Added `use_ai_for_all_posts` boolean field
  - `app/services/post_suggestion_service.py` - Looping logic + AI configuration
  - `app/static/calendar.html` - Default post count change
  - `app/static/restaurant-config.html` - AI toggle UI
  - `app/api/restaurant.py` - New settings endpoint
- Backend: 396 insertions, 19 deletions across 6 files

### Benefits
- **Cost Control**: Users can now control OpenAI costs by toggling AI usage
- **Flexibility**: Generate exactly the number of posts needed for monthly planning
- **Transparency**: Full visibility into OpenAI API interactions
- **Better Defaults**: 8 posts/month is more realistic for most restaurants

---

## [1.0.4] - 2025-12-30

### Fixed
- **OpenAI API Compatibility**: Updated from deprecated `openai.ChatCompletion.create()` to new OpenAI client API
  - Modified `RestaurantIntelligenceService` to use `OpenAI().chat.completions.create()`
  - Changed import from `import openai` to `from openai import OpenAI`
  - Updated initialization to create client instance
  - Fixed all 3 API calls in `restaurant_intelligence_service.py`
  - Ensures compatibility with openai>=1.0.0

- **AI Content Generation Parameter Error**: Fixed missing `text_length` parameter
  - Added `text_length: str = "extra_long"` parameter to `generate_post_caption()` method
  - Fixed NameError that was preventing post generation
  - Cleared Python bytecode cache to ensure proper code loading
  - Post generation now works correctly with text length controls

### Changed
- **Server Startup**: Cleared Python cache files for clean deployments
  - Removed all `__pycache__` directories
  - Deleted `.pyc` bytecode files
  - Ensures fresh code loading on server restart

### Technical Details
- Updated `app/services/restaurant_intelligence_service.py:83`
- Updated `app/services/content_generator.py:48`
- Compatible with OpenAI Python SDK v1.0.0+

### Testing
- Verified AI post generation works without errors
- Confirmed text length parameter defaults to "extra_long"
- Tested server restart with cache clearing
- Validated OpenAI API integration

---

## [1.0.3] - 2025-12-29

### Added
- **Monthly Content Calendar System**:
  - AI-generated monthly calendars with 20-30 strategically distributed posts
  - Smart post scheduling based on sales patterns and day of week
  - Visual calendar grid UI at `/ui/calendar`
  - Post type-based optimal timing:
    - Promotional posts: 10:00 AM (slow days)
    - Product showcases: 6:00 PM (dinner time)
    - Weekend drivers: 5:00 PM Friday
    - Engagement posts: 12:00 PM (lunch)
    - Customer appreciation: 3:00 PM
  - Approval workflow: draft → approved → published
  - Full CRUD operations for calendar posts
  - Month/year navigation with calendar generation
  - Post statistics: total, approved, published counts

- **Database Schema**:
  - `content_calendars` table for monthly calendar management
  - `calendar_posts` table for scheduled posts
  - Relationships with tenant isolation
  - Alembic migration: `20251228_2357_ee873fe5c1e6_add_content_calendar_tables.py`

- **API Endpoints**:
  - `POST /api/v1/restaurant/{tenant_id}/calendar/generate` - Generate monthly calendar
  - `GET /api/v1/restaurant/{tenant_id}/calendar/{year}/{month}` - Get calendar
  - `PUT /api/v1/restaurant/{tenant_id}/calendar/{calendar_id}/approve` - Approve all posts
  - `PUT /api/v1/restaurant/{tenant_id}/calendar/post/{post_id}` - Update post
  - `DELETE /api/v1/restaurant/{tenant_id}/calendar/post/{post_id}` - Delete post

- **Services**:
  - `ContentCalendarService` - Calendar generation and management
  - Strategic post distribution algorithm
  - Integration with `PostSuggestionService` for content generation
  - Smart scheduling based on restaurant sales data

- **UI Components**:
  - Calendar page with grid layout (`calendar.html`)
  - Month/year selector with generate button
  - Calendar stats dashboard
  - Post preview cards with color-coded statuses
  - Edit modal for post customization
  - Generate modal with configurable post count
  - Navigation integration across all pages
  - Featured calendar card on main dashboard

- **Restaurant Intelligence Enhancements**:
  - Added `statistics.orders_by_day_of_week` to sales insights
  - Day-by-day order counts and revenue tracking
  - Powers dashboard "Sales by Day of Week" chart
  - Enhanced `RestaurantIntelligenceService` template generation

### Changed
- **Dashboard UI**:
  - Updated navigation menu to include Calendar link
  - Added "Monthly Content Calendar" as primary featured card
  - Moved previous features to secondary cards
  - Fixed "Sales by Day of Week" chart (was empty)
  - Chart now displays order counts and revenue per day

- **Sales Insights Structure**:
  - Modified `_template_sales_insights()` in `restaurant_intelligence_service.py`
  - Added `statistics` field to sales insights JSON
  - Includes detailed day-of-week breakdown for analytics

- **Navigation**:
  - Consistent calendar links across all UI pages
  - Dashboard, Post Ideas, Calendar, Create Post, Config, Assets
  - Calendar featured prominently on dashboard

### Fixed
- **Dashboard Chart**:
  - "Sales by Day of Week" chart was displaying empty
  - Missing `statistics.orders_by_day_of_week` field in profile data
  - Chart now shows: Monday through Sunday with order counts and revenue
  - Properly displays busiest day (Saturday: 26 orders, $1,767)
  - Highlights slowest day (Thursday: 7 orders, $513)

### Database Migrations
- Migration `20251228_2357_ee873fe5c1e6` adds:
  - `content_calendars` table with year/month indexing
  - `calendar_posts` table with scheduling fields
  - Status tracking and approval workflow
  - Tenant isolation with CASCADE deletes

### Testing
- Generated test calendar for January 2025 with 6 posts
- Verified strategic post distribution across month
- Tested all CRUD operations (create, read, update, delete)
- Confirmed approval workflow functionality
- Validated chart data rendering on dashboard
- Calendar accessible at http://localhost:8000/ui/calendar

### Technical Details
- **Post Distribution Algorithm**: Evenly distributes posts using `interval = month_days / posts_count`
- **Strategic Timing**: Uses sales patterns (busiest_days, slowest_days) for optimal posting times
- **Multi-Status Tracking**: draft, approved, published, rejected, failed
- **Platform Support**: Facebook, Instagram, or both
- **Content Types**: promotional, product_showcase, weekend_traffic, engagement, customer_appreciation

### Known Improvements
- Calendar posts can be edited before approval
- Posts include: title, text, date, time, platform, hashtags, featured items
- Strategic scheduling considers restaurant-specific sales patterns
- Future: Auto-publish approved posts at scheduled time

---

## [1.0.2] - 2025-12-28

### Fixed
- **Image Posting to Facebook**: Images now appear correctly in Facebook posts
  - Implemented direct file upload instead of URL-based posting
  - Bypasses ngrok free tier interstitial page limitation
  - Reads local image files and uploads as multipart/form-data
  - Fixed bug in `app/api/posts.py` where `request.image_url` was used instead of `image_url` variable

### Added
- **ngrok Integration for Development**:
  - Set up ngrok tunnel to expose localhost:8000 to the internet
  - Configured public URL: `https://kristian-unrenewable-mercedez.ngrok-free.dev`
  - Updated environment variables to use ngrok URL
  - Created `NGROK_SETUP.md` documentation with setup instructions

### Changed
- **Image Posting Architecture**:
  - Modified `_post_to_facebook()` function in `app/api/posts.py`
  - Changed from URL-based image posting to direct file upload
  - Extract file path from image_url and read file bytes
  - Upload image data directly to Facebook Graph API
  - Added comprehensive error handling for file operations

### Infrastructure
- **Database URL Migration**:
  - Created `update_image_urls.py` utility script
  - Migrated 3 brand_assets URLs from localhost to ngrok
  - Migrated 6 post_history URLs from localhost to ngrok
  - Ensures existing images remain accessible

### Documentation
- Added ngrok setup guide (`NGROK_SETUP.md`)
- Documented image posting troubleshooting steps
- Added production migration notes (ngrok → AWS S3)

### Testing
- Successfully posted to Facebook with images
- Verified Facebook post ID: 122112052983135398
- Confirmed image appears in live Facebook post

---

## [1.0.1] - 2025-12-27 to 2025-12-28

### Added
- **Brand Asset Management System**:
  - Hierarchical folder structure for organizing restaurant images
  - Folders: Food (Pizza, Pasta, Appetizers, Desserts), Drinks, Restaurant, Seasonal
  - Asset upload with metadata and tagging support
  - Visual asset browser with grid layout in posting UI
  - Quick upload functionality for on-the-fly image uploads
  - Sidebar navigation for easy folder access
  - Support for JPEG, PNG, GIF, WebP formats

- **AI-Powered Content Generation**:
  - Integrated OpenAI GPT-4 for social media caption generation
  - Context-aware prompts using restaurant description and item details
  - Smart anti-repetition system that analyzes recent posts
  - Platform-specific optimization (Facebook vs Instagram)
  - Customizable tone (casual, professional, humorous, promotional, educational)
  - Maximum character length constraints
  - Automatic emoji and hashtag inclusion
  - Call-to-action generation

- **Database Models**:
  - `BrandAsset` model with metadata and tagging
  - `BrandFolder` model with hierarchical parent-child relationships
  - Asset-folder relationship tracking
  - Created and updated timestamps

- **API Endpoints**:
  - `POST /api/v1/tenants/{tenant_id}/init-folders` - Initialize folder structure
  - `GET /api/v1/tenants/{tenant_id}/folders` - List folders
  - `POST /api/v1/folders` - Create folder
  - `GET /api/v1/folders/{folder_id}/assets` - List assets
  - `POST /api/v1/folders/{folder_id}/assets` - Upload asset
  - `DELETE /api/v1/assets/{asset_id}` - Delete asset
  - `POST /api/v1/posts/generate` - Generate AI caption
  - `PUT /api/v1/assets/{asset_id}` - Update asset metadata

- **Services**:
  - `AssetService` for brand asset management
  - `ContentGeneratorService` for AI-powered caption generation
  - Integration with OpenAI API

- **UI Components**:
  - Asset picker modal in posting interface
  - "Browse Asset Library" button
  - "Quick Upload" button for direct uploads
  - Folder tree navigation in sidebar
  - Asset detail view with metadata editing

### Changed
- **Posting UI Enhanced**:
  - Added image selection from brand asset library
  - Integrated AI caption generation with custom parameters
  - Restaurant description and item details form fields
  - Tone selector for content generation
  - Platform selector (Facebook/Instagram)

- **OpenAI Configuration**:
  - Added `GPT_TEXT_MODEL` environment variable
  - Configurable model selection via .env
  - Fallback to template-based generation if API fails

- **Content Generation Logic**:
  - System message defines AI as creative social media manager
  - User prompt includes restaurant context
  - Recent post history for anti-repetition
  - Platform-specific optimization instructions

### Fixed
- Template-based vs AI-generated post differentiation
- OpenAI API key environment loading after .env updates
- Server restart required after environment changes

### Testing
- Uploaded 3 test images (pizza, pasta, chicken wings)
- Verified folder structure initialization
- Tested AI caption generation with OpenAI GPT-4
- Confirmed unique, contextual captions generated
- Validated asset picker UI functionality

### Known Issues
- Restaurant description currently hardcoded in `posting-ui.html:563`
- Should be moved to tenant configuration for multi-tenant support

---

## [1.0.0] - 2025-12-26

### Added - Initial Release
- **Multi-Tenant Architecture**:
  - Complete tenant isolation with dedicated data per restaurant
  - Support for 1,000+ concurrent tenants
  - Tiered plans: Basic, Pro, Enterprise
  - Per-tenant rate limiting and posting quotas

- **OAuth2 Authentication**:
  - Facebook OAuth 2.0 flow implementation
  - Instagram Business account connection
  - CSRF protection with state tokens
  - OAuth state management with 10-minute expiration
  - Secure redirect URI validation

- **Token Management**:
  - AES-256-GCM encryption for all OAuth tokens
  - Automatic token refresh before expiration
  - Token health monitoring and status tracking
  - Background jobs for proactive token refresh
  - Token expiration alerts
  - Refresh token rotation

- **Database Schema**:
  - `tenants` - Restaurant accounts
  - `tenant_users` - Admin users per tenant
  - `social_accounts` - Connected Facebook/Instagram accounts
  - `oauth_tokens` - Encrypted access and refresh tokens
  - `token_refresh_history` - Audit log of token operations
  - `post_history` - Complete posting history
  - `webhook_events` - Platform webhook events
  - `oauth_state` - CSRF protection tokens

- **Core Services**:
  - `OAuthService` - OAuth flow handling
  - `TokenService` - Token lifecycle management
  - `EncryptionService` - AES-256-GCM encryption
  - `PostingService` - Multi-tenant posting (placeholder)

- **API Endpoints**:
  - `POST /api/v1/tenants` - Register new tenant
  - `GET /api/v1/oauth/facebook/authorize` - Start OAuth
  - `GET /api/v1/oauth/facebook/callback` - OAuth callback
  - `GET /api/v1/tenants/{tenant_id}/accounts` - List accounts
  - `DELETE /api/v1/accounts/{account_id}` - Disconnect account
  - `GET /api/v1/accounts/{account_id}/token-health` - Token status
  - `POST /api/v1/tokens/refresh` - Manual token refresh

- **Background Jobs (Celery)**:
  - Automatic token refresh (runs every 24 hours)
  - OAuth state cleanup (runs every hour)
  - Token expiration monitoring
  - Failed refresh retry logic

- **Infrastructure**:
  - FastAPI application with CORS support
  - PostgreSQL database with SQLAlchemy 2.0 ORM
  - Redis for caching and Celery task queue
  - Celery Beat scheduler for periodic tasks
  - Structured logging system

- **Security Features**:
  - Token encryption at rest
  - CSRF protection for OAuth flow
  - Secure token storage
  - Per-tenant data isolation
  - Rate limiting per plan tier

- **Health Checks**:
  - `GET /health` - API health status
  - `GET /health/db` - Database connectivity
  - `GET /health/redis` - Redis connectivity

- **Documentation**:
  - `SESSION_LOG.md` - Development session tracking
  - `CONVERSATION_LOG.md` - Complete conversation history
  - `QUICKSTART.md` - 30-minute setup guide
  - `FACEBOOK_APP_SETUP.md` - Facebook app configuration
  - `DATABASE_SETUP.md` - Database setup instructions
  - `ENVIRONMENT_SETUP.md` - Environment configuration
  - Interactive API docs (Swagger UI, ReDoc)

### Technical Stack
- **Backend**: FastAPI 0.104+, Python 3.11+
- **Database**: PostgreSQL 14+ with SQLAlchemy 2.0
- **Cache/Queue**: Redis 7+
- **Task Queue**: Celery 5+ with Beat
- **Encryption**: cryptography library (AES-256-GCM)
- **OAuth**: Facebook Graph API v18.0
- **Logging**: Python logging module

### Testing
- Successfully registered first tenant (Krusty Pizza)
- Completed OAuth flow with Facebook
- Connected Facebook Pages
- Verified token encryption and storage
- Tested automatic token refresh
- Confirmed health check endpoints
- Validated CSRF protection

---

## Release Notes

### Version Naming Convention
- **Major.Minor.Patch** (Semantic Versioning)
- **Major**: Breaking changes or major feature releases
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes and minor improvements

### Support Policy
- **Latest version**: Full support with bug fixes and features
- **Previous version**: Security fixes only
- **Older versions**: Community support via GitHub issues

---

## Migration Guides

### Migrating from v1.0.0 to v1.0.1
1. Pull latest code from git
2. No database schema changes required
3. Add `OPENAI_API_KEY` to .env (optional)
4. Add `GPT_TEXT_MODEL=gpt-4` to .env
5. Restart FastAPI server
6. Initialize folder structure for existing tenants:
   ```bash
   curl -X POST http://localhost:8000/api/v1/tenants/{tenant_id}/init-folders
   ```

### Migrating from v1.0.1 to v1.0.2
1. Pull latest code from git
2. No database schema changes required
3. Set up ngrok (development) or S3 (production) for image hosting
4. Update .env with new `API_URL` and `PUBLIC_URL`
5. Run `update_image_urls.py` to migrate existing image URLs
6. Restart FastAPI server
7. Test image posting to verify fix

---

## Contributors

- Claude (AI Assistant) - Implementation, documentation, architecture
- Asif Rao - Product owner, requirements, testing, feedback

---

## License

Copyright 2025. All rights reserved.
