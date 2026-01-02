# Feature Documentation - Social Automation Platform v2.1.1

## Overview
Multi-tenant restaurant social media automation platform with AI-powered content generation, strategic scheduling, and comprehensive analytics.

---

## ✅ Completed Features

### 1. Multi-Tenant Architecture
**Status**: ✅ Complete
**Version**: 1.0.0

**Description**: Complete tenant isolation with dedicated data per restaurant.

**Components**:
- Tenant registration and management
- Per-tenant data isolation
- Tiered plans: Basic, Pro, Enterprise
- Rate limiting per plan
- User management per tenant

**Database Tables**:
- `tenants` - Restaurant accounts
- `tenant_users` - Admin users

**API Endpoints**:
- `POST /api/v1/tenants` - Register new tenant
- `GET /api/v1/tenants/{tenant_id}` - Get tenant details

**Files**:
- `app/models/tenant.py`
- `app/api/tenants.py`

---

### 2. OAuth2 Authentication
**Status**: ✅ Complete
**Version**: 1.0.0

**Description**: Secure Facebook and Instagram OAuth flow with token encryption.

**Components**:
- Facebook OAuth 2.0 implementation
- Instagram Business account connection
- CSRF protection with state tokens
- OAuth state management (10-minute expiration)
- Secure redirect URI validation

**Security Features**:
- AES-256-GCM token encryption
- Automatic token refresh
- Token health monitoring
- Refresh token rotation

**Database Tables**:
- `social_accounts` - Connected accounts
- `oauth_tokens` - Encrypted tokens
- `oauth_state` - CSRF protection
- `token_refresh_history` - Audit log

**API Endpoints**:
- `GET /api/v1/oauth/facebook/authorize` - Start OAuth
- `GET /api/v1/oauth/facebook/callback` - OAuth callback
- `GET /api/v1/tenants/{tenant_id}/accounts` - List accounts
- `DELETE /api/v1/accounts/{account_id}` - Disconnect account
- `GET /api/v1/accounts/{account_id}/token-health` - Token status
- `POST /api/v1/tokens/refresh` - Manual refresh

**Services**:
- `OAuthService` - OAuth flow handling
- `TokenService` - Token lifecycle
- `EncryptionService` - AES-256-GCM encryption

**Files**:
- `app/services/oauth_service.py`
- `app/services/token_service.py`
- `app/utils/encryption.py`
- `app/api/oauth.py`
- `app/api/accounts.py`

---

### 3. Restaurant Intelligence System
**Status**: ✅ Complete
**Version**: 1.0.1 (Enhanced in 1.0.3)

**Description**: AI-powered analysis of restaurant data to generate insights and content strategies.

**Components**:
- Menu item analysis
- Sales pattern recognition
- Brand personality analysis
- Content strategy generation
- Day-of-week sales statistics

**Analysis Outputs**:
- **Brand Analysis**:
  - Cuisine type and style
  - Signature items
  - Target audience
  - Voice and tone recommendations

- **Sales Insights** (v1.0.3):
  - Busiest/slowest days
  - Peak hours
  - Top sellers
  - Underperforming items
  - **Statistics**: Orders by day of week with revenue

- **Content Strategy**:
  - Posting frequency
  - Best days/times to post
  - Content mix percentages
  - Post themes and ideas

**Database Tables**:
- `restaurant_profiles` - Profile with JSONB insights
- `menu_items` - Menu catalog with popularity
- `sales_data` - Sales transactions

**API Endpoints**:
- `GET /api/v1/restaurant/{tenant_id}/profile` - Get profile
- `POST /api/v1/restaurant/{tenant_id}/import/menu` - Import menu
- `POST /api/v1/restaurant/{tenant_id}/import/sales` - Import sales

**Services**:
- `RestaurantIntelligenceService` - AI/template analysis
- `MenuImportService` - Excel import
- `SalesImportService` - Sales import

**Files**:
- `app/services/restaurant_intelligence_service.py`
- `app/services/menu_import_service.py`
- `app/services/sales_import_service.py`
- `app/models/restaurant_profile.py`
- `app/models/menu_item.py`
- `app/models/sales_data.py`

---

### 4. AI Post Suggestion System
**Status**: ✅ Complete
**Version**: 1.0.1

**Description**: Generate context-aware social media post suggestions based on restaurant data.

**Components**:
- OpenAI GPT-4 integration
- Template-based fallback
- Anti-repetition system
- Multiple post types
- Platform optimization
- Hashtag suggestions

**Post Types**:
- Promotional
- Product Showcase
- Weekend Traffic Driver
- Engagement
- Customer Appreciation

**Features**:
- Analyzes recent posts to avoid repetition
- Uses restaurant insights for context
- Featured items from menu
- Strategic timing recommendations
- Platform-specific content

**API Endpoints**:
- `POST /api/v1/restaurant/{tenant_id}/suggestions` - Generate suggestions

**Services**:
- `PostSuggestionService` - Suggestion generation

**UI**:
- `/ui/suggestions` - Post suggestions interface

**Files**:
- `app/services/post_suggestion_service.py`
- `app/static/post-suggestions.html`

---

### 5. Monthly Content Calendar
**Status**: ✅ Complete
**Version**: 2.1.1 (Enhanced - Hybrid Scheduling)

**Description**: AI-generated monthly calendars with hybrid day-of-week scheduling, strategic distribution, and configurable AI usage.

**Components**:
- Monthly calendar generation (5-31 posts, default: 8, recommended: 8-15)
- Dynamic post count generation - generates exactly the requested number
- **Hybrid day-of-week scheduling** - posts land on strategically optimal days
- Smart scheduling respects marketing strategy (target_day from suggestions)
- Visual calendar grid UI
- Approval workflow
- Full CRUD operations
- **NEW**: Configurable AI usage toggle for cost control
- **NEW**: Complete OpenAI request/response logging
- **NEW**: Real-time generation progress tracking

**Strategic Scheduling** (v2.1.1):
- **Promotional posts**: Thursdays (slow days) at 10:00 AM
- **Product showcases**: Tuesdays at 6:00 PM (dinner time)
- **Weekend drivers**: Fridays at 5:00 PM (drive weekend traffic!)
- **Engagement posts**: Wednesdays at 12:00 PM (mid-week engagement)
- **Customer appreciation**: Thursdays at 3:00 PM
- Posts distribute across different weeks (no clustering on same days)

**AI Configuration Modes** (v2.1.0):
- **Mixed Mode** (Default, `use_ai_for_all_posts = False`):
  - Promotional posts → AI ✅
  - Product showcase posts → AI ✅
  - Weekend driver posts → AI ✅
  - Engagement posts → Template 📝
  - Customer appreciation posts → Template 📝
  - **Cost**: ~4-6 OpenAI calls for 8 posts

- **Full AI Mode** (`use_ai_for_all_posts = True`):
  - All post types → AI ✅
  - **Cost**: 8 OpenAI calls for 8 posts
  - Higher quality, higher costs
  - Configured via Restaurant Config UI toggle

**Workflow**:
1. Configure AI usage in Restaurant Config (optional)
2. Generate calendar for month/year with desired post count
3. Monitor real-time generation progress with detailed logs
4. Review posts in calendar grid
5. View complete OpenAI request/response data (if enabled in Developer Mode)
6. Edit individual posts (text, date, time, platform, hashtags)
7. Approve all posts
8. Posts ready for publishing

**Database Tables**:
- `content_calendars` - Monthly calendars
- `calendar_posts` - Individual scheduled posts

**API Endpoints**:
- `POST /api/v1/restaurant/{tenant_id}/calendar/generate` - Generate
- `GET /api/v1/restaurant/{tenant_id}/calendar/{year}/{month}` - Get calendar
- `PUT /api/v1/restaurant/{tenant_id}/calendar/{calendar_id}/approve` - Approve all
- `PUT /api/v1/restaurant/{tenant_id}/calendar/post/{post_id}` - Update post
- `DELETE /api/v1/restaurant/{tenant_id}/calendar/post/{post_id}` - Delete post

**Services**:
- `ContentCalendarService` - Calendar management

**UI**:
- `/ui/calendar` - Calendar interface with grid view

**Files**:
- `app/services/content_calendar_service.py`
- `app/models/content_calendar.py`
- `app/models/calendar_post.py`
- `app/static/calendar.html`
- Migration: `20251228_2357_ee873fe5c1e6_add_content_calendar_tables.py`

---

### 6. Manual Post Creation
**Status**: ✅ Complete
**Version**: 1.0.1

**Description**: Create and schedule individual posts with AI caption generation.

**Components**:
- Manual post creation form
- AI caption generation
- Brand asset selection
- Image upload
- Platform selection (Facebook/Instagram/Both)
- Scheduling for future publication

**Features**:
- Generate AI captions with context
- Browse brand asset library
- Quick upload new images
- Tone selector (casual, professional, humorous, etc.)
- Platform optimization
- Schedule for specific date/time

**API Endpoints**:
- `POST /api/v1/posts` - Create post
- `POST /api/v1/posts/generate` - Generate caption
- `GET /api/v1/posts/history` - Post history

**Services**:
- `PostService` - Post creation and publishing
- `ContentGenerator` - AI caption generation

**UI**:
- `/ui/create` - Create post interface
- Asset picker modal
- Caption generator

**Files**:
- `app/services/post_service.py`
- `app/services/content_generator.py`
- `app/static/create-post.html`
- `app/models/post.py`

---

### 7. Brand Asset Management
**Status**: ✅ Complete
**Version**: 1.0.1

**Description**: Organize and manage restaurant images in hierarchical folders.

**Components**:
- Hierarchical folder structure
- Image upload with metadata
- Asset tagging and categorization
- Visual browser interface
- Quick upload functionality

**Default Folders**:
- Food
  - Pizza
  - Pasta
  - Appetizers
  - Desserts
- Drinks
- Restaurant
- Seasonal

**Features**:
- Folder tree navigation
- Grid view of assets
- Metadata editing
- Tag management
- Asset search and filtering
- Image preview

**Database Tables**:
- `brand_assets` - Images with metadata
- `asset_folders` - Hierarchical folders

**API Endpoints**:
- `POST /api/v1/tenants/{tenant_id}/init-folders` - Initialize folders
- `GET /api/v1/tenants/{tenant_id}/folders` - List folders
- `POST /api/v1/folders` - Create folder
- `GET /api/v1/folders/{folder_id}/assets` - List assets
- `POST /api/v1/folders/{folder_id}/assets` - Upload asset
- `PUT /api/v1/assets/{asset_id}` - Update metadata
- `DELETE /api/v1/assets/{asset_id}` - Delete asset

**Services**:
- `AssetService` - Asset management
- `FolderService` - Folder operations

**UI**:
- `/ui/assets` - Asset library interface
- Asset picker for post creation

**Files**:
- `app/services/asset_service.py`
- `app/services/folder_service.py`
- `app/models/brand_asset.py`
- `app/models/asset_folder.py`
- `app/static/asset-library.html`

---

### 8. Dashboard & Analytics
**Status**: ✅ Complete
**Version**: 1.0.3

**Description**: Central dashboard with restaurant analytics and feature navigation.

**Components**:
- Restaurant statistics
- Sales by day of week chart
- Top 5 menu items chart
- Feature navigation cards
- Quick access to all features

**Statistics Displayed**:
- Menu items count
- Sales records count
- Top seller with order count
- Slowest day with order count

**Charts** (v1.0.3 Fixed):
- **Sales by Day of Week**: Bar chart showing orders and revenue per day
- **Top 5 Menu Items**: Ranked list with order counts

**Navigation Cards**:
- Monthly Content Calendar (featured)
- AI Post Suggestions
- Create Post
- Restaurant Config
- Brand Assets

**UI**:
- `/ui` - Main dashboard

**Files**:
- `app/static/dashboard.html`

---

### 9. Restaurant Configuration
**Status**: ✅ Complete
**Version**: 2.1.0 (Enhanced)

**Description**: Upload and manage restaurant data (menu, sales) and configure AI settings.

**Components**:
- Menu Excel upload
- Sales Excel upload
- Profile viewing
- Data import status
- **NEW**: Developer Mode toggle (view OpenAI prompts)
- **NEW**: AI for All Posts toggle (cost control)

**Supported Formats**:
- Menu: Excel (.xlsx) with columns: Category, Item Name, Description, Price
- Sales: Excel (.xlsx) with order data

**Features**:
- Drag-and-drop upload
- Import progress indication
- Automatic intelligence regeneration
- Data validation
- **NEW**: Toggle switches for AI configuration
- **NEW**: Real-time settings persistence

**Configuration Options** (v2.1.0):
1. **Developer Mode**: View OpenAI prompts before they're sent (debugging/transparency)
2. **Use AI for All Posts**: Generate all posts with AI vs mixed template/AI mode

**UI**:
- `/ui/config` - Configuration interface with AI toggles

**API Endpoints**:
- `POST /api/v1/restaurant/{tenant_id}/settings/toggle-prompt-preview`
- `POST /api/v1/restaurant/{tenant_id}/settings/toggle-ai-for-all`

**Files**:
- `app/static/restaurant-config.html`
- `app/api/restaurant.py`

---

## 🔄 Background Services

### Celery Tasks
**Status**: ✅ Complete
**Version**: 1.0.0

**Tasks**:
- **Token Refresh**: Runs every 24 hours
- **OAuth State Cleanup**: Runs hourly
- **Failed Refresh Retry**: Automatic retry logic

**Configuration**:
- Redis as message broker
- Celery Beat for scheduling
- Task monitoring and logging

**Files**:
- `app/tasks/token_refresh.py`
- `app/celeryconfig.py`

---

## 📊 Current System Status (v2.1.1)

### Fully Operational Features:
1. ✅ Multi-tenant architecture
2. ✅ OAuth2 authentication (Facebook)
3. ✅ Token encryption and management
4. ✅ Restaurant intelligence system
5. ✅ AI post suggestions
6. ✅ Monthly content calendar with configurable AI usage
7. ✅ Manual post creation
8. ✅ Brand asset management
9. ✅ Dashboard with analytics
10. ✅ Restaurant configuration with AI settings

### Total Database Tables: 16
- tenants, tenant_users
- social_accounts, oauth_tokens, oauth_state, token_refresh_history
- restaurant_profiles, menu_items, sales_data
- brand_assets, asset_folders
- content_calendars, calendar_posts
- post_history, webhook_events

### Total API Endpoints: 40+
### Total UI Pages: 6
- Dashboard (`/ui`)
- Post Suggestions (`/ui/suggestions`)
- Content Calendar (`/ui/calendar`)
- Create Post (`/ui/create`)
- Restaurant Config (`/ui/config`)
- Asset Library (`/ui/assets`)

---

## 🚀 Next Steps / Future Enhancements

### High Priority:
1. **Automated Publishing**:
   - Publish approved calendar posts at scheduled time
   - Celery task for scheduled publishing
   - Post success/failure tracking

2. **Instagram Posting**:
   - Test Instagram Business API integration
   - Image posting to Instagram
   - Caption and hashtag optimization

3. **Analytics & Reporting**:
   - Post engagement tracking
   - Reach and impressions
   - Best performing content analysis
   - Monthly performance reports

### Medium Priority:
4. **Team Collaboration**:
   - Multi-user roles (owner, admin, manager, staff)
   - Approval workflows
   - Comment and feedback system

5. **Advanced Features**:
   - Multi-image carousel posts
   - Video posting support
   - Story posting
   - Post templates library

### Low Priority:
6. **Platform Expansion**:
   - Twitter/X integration
   - LinkedIn integration
   - TikTok integration

7. **Production Readiness**:
   - AWS S3 for image storage
   - CDN integration
   - Performance optimization
   - Load balancing

---

## 📝 Notes for Next Session

### Key Files to Review:
- `CHANGELOG.md` - Version history
- `FEATURES.md` - This file (feature documentation)
- `README.md` - Project overview
- `ARCHITECTURE.md` - System architecture

### Important Endpoints:
- Dashboard: `http://localhost:8000/ui`
- Calendar: `http://localhost:8000/ui/calendar`
- API Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

### Test Tenant:
- ID: `1485f8b4-04e9-47b7-ad8a-27adbe78d20a`
- Name: Krusti Pizza & Pasta
- Has menu (57 items), sales (97 records), and profile

### Environment:
- PostgreSQL database running
- Redis running
- FastAPI server with auto-reload
- ngrok tunnel for development

### Recent Additions (v2.1.1):
- **Hybrid Day-of-Week Scheduling**: Posts now land on strategically optimal days
- **Fixed Sunday/Wednesday Clustering**: No more posts concentrated on 2 days
- **Target Day Respect**: Weekend posts on Fridays, engagement on Wednesdays, etc.
- **Smart Distribution**: Multiple posts wanting same day spread across different weeks
- **Fallback Logic**: Adjacent day selection when preferred day is full
- **Strategic Placement**: Single posts use middle occurrence for better spacing

### Previous Additions (v2.1.0):
- **Configurable AI Usage**: Toggle between full AI mode and mixed template/AI mode
- **Dynamic Post Count**: Generate exactly the requested number of posts (5-31)
- **Default Post Count**: Changed from 25 to 8 (more realistic for monthly planning)
- **AI Cost Control**: "Use AI for All Posts" toggle in Restaurant Config
- **Complete Transparency**: Full OpenAI request/response logging
- **Real-time Progress**: Generation progress tracking with detailed logs
- **Enhanced Post Variety**: Looping logic creates diverse posts until target count

### Additions (v1.0.3):
- Monthly content calendar fully functional
- Dashboard chart fixed
- Sales insights enhanced with statistics
- All UI pages updated with calendar navigation

---

**Last Updated**: 2026-01-02
**Version**: 2.1.1
**Status**: Production-ready for restaurant social media automation with strategic day-of-week scheduling
