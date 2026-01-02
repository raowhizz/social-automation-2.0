#!/usr/bin/env python3
"""
Create a New Year's post for Krusty Pizza & Pasta
"""
import sys
from pathlib import Path
from datetime import datetime
import requests

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "multi-tenant-oauth"))
from oauth_integration import MultiTenantPosterFactory, OAuthTokenManager

# Tenant configuration
TENANT_ID = "1485f8b4-04e9-47b7-ad8a-27adbe78d20a"  # Krusty Pizza & Pasta

def main():
    print("=" * 60)
    print("CREATING NEW YEAR'S POST FOR KRUSTY PIZZA & PASTA")
    print("=" * 60)

    # Step 1: Check OAuth status
    print("\n📊 Step 1: Checking OAuth status...")
    with OAuthTokenManager(TENANT_ID) as manager:
        health = manager.get_token_health()
        accounts = manager.get_account_info()

        print(f"   Active tokens: {health['active_tokens']}")
        print(f"   Connected accounts:")
        for acc in accounts:
            print(f"     • {acc['account_name']} ({acc['platform']})")

        if health['active_tokens'] == 0:
            print("\n❌ No active tokens! Run OAuth flow first.")
            return

    # Step 2: Create OAuth-powered poster
    print("\n🔧 Step 2: Creating OAuth-powered FacebookPoster...")
    try:
        poster = MultiTenantPosterFactory.create_facebook_poster(TENANT_ID)
        print(f"   ✅ Poster created successfully!")
        print(f"   Page ID: {poster.page_id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # Step 3: Create New Year's message
    print("\n📝 Step 3: Creating New Year's post...")

    message = """🎉🍕 HAPPY NEW YEAR from Krusty Pizza & Pasta! 🍝🎊

Cheers to a delicious 2026 filled with:
✨ Fresh, hot pizza straight from our oven
✨ Perfectly crafted pasta dishes
✨ Great times with family and friends
✨ Amazing flavors in every bite

Thank you for making us part of your special moments in 2025. We can't wait to serve you even more incredible meals in the year ahead!

🎆 Ring in the New Year with our special menu - Order now for delivery or pickup!

📞 Call us or order online
🍕 Fresh ingredients, authentic taste
❤️ Made with love, served with a smile

Here's to another year of pizza perfection! 🥂

#HappyNewYear #NewYear2026 #KrustyPizza #PizzaAndPasta #FreshPizza #ItalianFood #PizzaLovers #NewYearCelebration #Cheers2026"""

    print(f"   Message length: {len(message)} chars")

    # Step 4: Post to Facebook
    print(f"\n📤 Step 4: Posting to Facebook...")
    try:
        url = f"https://graph.facebook.com/v18.0/{poster.page_id}/feed"
        data = {
            "message": message,
            "access_token": poster.access_token
        }

        response = requests.post(url, data=data)
        result = response.json()

        if 'id' in result:
            post_id = result['id']
            print(f"\n✅ POST SUCCESSFUL!")
            print(f"   Post ID: {post_id}")
            post_url = f"https://www.facebook.com/{post_id.replace('_', '/posts/')}"
            print(f"   URL: {post_url}")

            # Open in browser
            import subprocess
            subprocess.run(['open', post_url], check=False)

        else:
            error = result.get('error', {})
            print(f"\n❌ POST FAILED!")
            print(f"   Error: {error.get('message', 'Unknown error')}")
            print(f"   Code: {error.get('code', 'N/A')}")

    except Exception as e:
        print(f"\n❌ Error posting: {e}")

    print("\n" + "=" * 60)
    print("✅ New Year's post complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
