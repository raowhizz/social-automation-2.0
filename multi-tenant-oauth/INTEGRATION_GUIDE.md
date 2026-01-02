## OAuth Integration Guide

Complete guide for integrating the multi-tenant OAuth system with your existing posting workflow.

---

## Quick Start

### Option 1: Use the Factory (Recommended)

The easiest way - just replace your existing poster creation:

```python
# OLD WAY (hardcoded tokens in config)
from social_poster import FacebookPoster
poster = FacebookPoster()

# NEW WAY (OAuth tokens from database)
import sys
sys.path.insert(0, 'multi-tenant-oauth')
from oauth_integration import MultiTenantPosterFactory

poster = MultiTenantPosterFactory.create_facebook_poster(
    tenant_id="1485f8b4-04e9-47b7-ad8a-27adbe78d20a"
)

# Use exactly the same way as before!
result = poster.post_photo(image_path, caption="Test post")
```

### Option 2: Manual Token Retrieval

If you need more control:

```python
import sys
sys.path.insert(0, 'multi-tenant-oauth')
from oauth_integration import OAuthTokenManager

# Get token
with OAuthTokenManager(tenant_id="abc-123") as manager:
    token = manager.get_facebook_token()
    print(f"Token: {token[:20]}...")

    # Get account info
    accounts = manager.get_account_info(platform="facebook")
    for account in accounts:
        print(f"Account: {account['account_name']}")
```

---

## Integration Examples

### Example 1: Update main.py for Single Tenant

Add OAuth support to your existing `main.py`:

```python
#!/usr/bin/env python3
"""
Updated main.py with OAuth integration
"""
import sys
from pathlib import Path

# Add multi-tenant-oauth to path
sys.path.insert(0, str(Path(__file__).parent / "multi-tenant-oauth"))
from oauth_integration import MultiTenantPosterFactory, OAuthTokenManager

# Your existing code...
from src.config import Config, RestaurantConfig
from src.content_generator import ContentGenerator

def main():
    # Configure tenant
    TENANT_ID = "1485f8b4-04e9-47b7-ad8a-27adbe78d20a"  # Test Restaurant

    # Check token health before posting
    with OAuthTokenManager(TENANT_ID) as manager:
        health = manager.get_token_health()
        print(f"Token Health: {health['active_tokens']} active tokens")

        if health['active_tokens'] == 0:
            print("ERROR: No active tokens! Please run OAuth flow first.")
            return

    # Generate content (your existing code)
    restaurant = RestaurantConfig("krusty_pizza")
    generator = ContentGenerator()

    # Create OAuth-powered poster (replaces old FacebookPoster)
    facebook_poster = MultiTenantPosterFactory.create_facebook_poster(TENANT_ID)

    # Post as usual!
    result = facebook_poster.post_photo(
        image_path=Path("output/facebook/image.jpg"),
        caption="Check out our daily special!"
    )

    if result["success"]:
        print(f"Posted successfully! ID: {result['post_id']}")
    else:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
```

### Example 2: Multi-Tenant Posting Loop

Post to multiple restaurants:

```python
#!/usr/bin/env python3
"""
Post to multiple restaurants using OAuth
"""
import sys
sys.path.insert(0, "multi-tenant-oauth")
from oauth_integration import MultiTenantPosterFactory, OAuthTokenManager

# List of tenant IDs (restaurants)
TENANTS = {
    "test_restaurant": "1485f8b4-04e9-47b7-ad8a-27adbe78d20a",
    "pizza_place": "another-tenant-id-here",
    "burger_joint": "yet-another-tenant-id",
}

def post_to_all_restaurants(image_path, caption):
    """Post the same content to all restaurants."""
    results = {}

    for restaurant_name, tenant_id in TENANTS.items():
        print(f"\nPosting to {restaurant_name}...")

        try:
            # Create poster for this tenant
            poster = MultiTenantPosterFactory.create_facebook_poster(tenant_id)

            # Post
            result = poster.post_photo(image_path, caption)
            results[restaurant_name] = result

            if result["success"]:
                print(f"  ✅ Success! Post ID: {result['post_id']}")
            else:
                print(f"  ❌ Failed: {result['error']}")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[restaurant_name] = {"success": False, "error": str(e)}

    return results

# Usage
results = post_to_all_restaurants(
    image_path="output/promo.jpg",
    caption="Weekend Special! 🍕"
)
```

### Example 3: Campaign-Based Multi-Tenant Posting

Integrate with your campaign system:

```python
#!/usr/bin/env python3
"""
Run campaigns for multiple tenants using OAuth
"""
import sys
from pathlib import Path
sys.path.insert(0, "multi-tenant-oauth")
from oauth_integration import MultiTenantPosterFactory, OAuthTokenManager

# Your existing imports
from src.campaign_manager import CampaignManager
from src.content_generator import ContentGenerator

def run_campaign_for_tenant(tenant_id, campaign_name, num_posts=3):
    """Run a campaign for a specific tenant."""

    # Check token health first
    with OAuthTokenManager(tenant_id) as manager:
        health = manager.get_token_health()
        accounts = manager.get_account_info()

        print(f"\nTenant Token Health:")
        print(f"  Active tokens: {health['active_tokens']}")
        print(f"  Accounts: {[a['account_name'] for a in accounts]}")

        if health['active_tokens'] == 0:
            print("  ⚠️ No active tokens - skipping this tenant")
            return

    # Load campaign
    campaign_manager = CampaignManager()
    campaign = campaign_manager.get_campaign(campaign_name)

    # Generate content
    generator = ContentGenerator()
    posts = generator.generate_campaign_posts(campaign, num_posts)

    # Create OAuth poster
    facebook_poster = MultiTenantPosterFactory.create_facebook_poster(tenant_id)

    # Post each item
    for i, post in enumerate(posts, 1):
        print(f"\n  Post {i}/{num_posts}...")
        result = facebook_poster.post_photo(
            image_path=post['image_path'],
            caption=post['caption']
        )

        if result["success"]:
            print(f"    ✅ Posted: {result['post_id']}")
        else:
            print(f"    ❌ Failed: {result['error']}")

# Run for all tenants
TENANTS = {
    "Krusty Pizza": "1485f8b4-04e9-47b7-ad8a-27adbe78d20a",
}

for name, tenant_id in TENANTS.items():
    print(f"\n{'='*60}")
    print(f"Running campaign for: {name}")
    print('='*60)

    run_campaign_for_tenant(
        tenant_id=tenant_id,
        campaign_name="weekend_special",
        num_posts=3
    )
```

---

## Managing Multiple Accounts per Tenant

If a restaurant has multiple Facebook Pages or Instagram accounts:

```python
from oauth_integration import OAuthTokenManager

with OAuthTokenManager(tenant_id="abc-123") as manager:
    # Get all Facebook accounts
    facebook_accounts = manager.get_account_info(platform="facebook")

    for account in facebook_accounts:
        print(f"\nAccount: {account['account_name']}")
        print(f"  ID: {account['id']}")
        print(f"  Platform ID: {account['platform_account_id']}")

        # Create poster for specific account
        from oauth_integration import MultiTenantPosterFactory
        poster = MultiTenantPosterFactory.create_facebook_poster(
            tenant_id="abc-123",
            account_id=account['id']  # Specify which account
        )

        # Post to this specific account
        result = poster.post_photo(image_path, caption)
```

---

## Error Handling

Always check token health before posting:

```python
from oauth_integration import OAuthTokenManager

def safe_post(tenant_id, image_path, caption):
    """Post with error handling and health checks."""

    # Check health
    with OAuthTokenManager(tenant_id) as manager:
        health = manager.get_token_health()

        if health['expired'] > 0:
            print(f"⚠️ Warning: {health['expired']} expired tokens")

        if health['expiring_soon'] > 0:
            print(f"⚠️ Warning: {health['expiring_soon']} tokens expiring soon")

        if health['active_tokens'] == 0:
            raise ValueError("No active tokens available for this tenant")

    # Create poster
    try:
        poster = MultiTenantPosterFactory.create_facebook_poster(tenant_id)
    except ValueError as e:
        print(f"Error creating poster: {e}")
        print("Please run OAuth flow to connect accounts.")
        return None

    # Post
    result = poster.post_photo(image_path, caption)

    if not result["success"]:
        print(f"Posting failed: {result.get('error', 'Unknown error')}")

    return result
```

---

## Migration Checklist

### ✅ Step 1: Update Imports

Replace:
```python
from social_poster import FacebookPoster
poster = FacebookPoster()
```

With:
```python
import sys
sys.path.insert(0, 'multi-tenant-oauth')
from oauth_integration import MultiTenantPosterFactory

poster = MultiTenantPosterFactory.create_facebook_poster(tenant_id="...")
```

### ✅ Step 2: Add Tenant Configuration

Add tenant ID configuration:
```python
# At top of main.py or config.py
TENANT_ID = "1485f8b4-04e9-47b7-ad8a-27adbe78d20a"  # Test Restaurant
```

### ✅ Step 3: Add Health Checks

Before posting loops:
```python
with OAuthTokenManager(TENANT_ID) as manager:
    health = manager.get_token_health()
    if health['active_tokens'] == 0:
        raise ValueError("No active tokens!")
```

### ✅ Step 4: Test

Run your posting workflow:
```bash
python main.py --restaurant krusty_pizza --campaign weekend_special --post
```

---

## Advanced Features

### Token Refresh

The system automatically tracks token usage and updates `last_used_at`. Background jobs (Celery) can auto-refresh expiring tokens:

```bash
# Start Celery worker (optional)
celery -A app.tasks.celery_app worker -l info

# Start Celery beat scheduler (optional)
celery -A app.tasks.celery_app beat -l info
```

### Posting History

All posts are automatically logged when using the OAuth system. Check:
```bash
psql social_automation_multi_tenant -c "SELECT * FROM post_history LIMIT 10;"
```

---

## Troubleshooting

### "No active tokens found"

Run OAuth flow to connect accounts:
```bash
curl -X POST http://localhost:8000/api/v1/oauth/facebook/authorize \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "YOUR_TENANT_ID", "return_url": "http://localhost:8000/"}'
```

### "Token expired"

Check token health:
```python
with OAuthTokenManager(tenant_id) as manager:
    health = manager.get_token_health()
    print(health)
```

If expired, reconnect via OAuth or manually refresh in database.

### "Account not found"

List available accounts:
```python
with OAuthTokenManager(tenant_id) as manager:
    accounts = manager.get_account_info()
    for acc in accounts:
        print(f"{acc['account_name']} - {acc['platform']}")
```

---

## Summary

**Minimal Changes Required:**
1. Add `import` for OAuth integration
2. Replace `FacebookPoster()` with `MultiTenantPosterFactory.create_facebook_poster(tenant_id)`
3. Add tenant ID configuration
4. Optionally add health checks

**Everything else stays the same!** Your existing posting code, image generation, campaign management, etc. all work without modification.

The OAuth system provides:
- ✅ Secure token storage (encrypted)
- ✅ Multi-tenant support (unlimited restaurants)
- ✅ Automatic token refresh
- ✅ Health monitoring
- ✅ Posting history tracking
