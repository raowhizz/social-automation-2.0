#!/usr/bin/env python3
"""
Test posting to Facebook Page using OAuth token from multi-tenant system.
"""

import requests
from datetime import datetime
from app.services import TokenService
from app.models.base import SessionLocal

# Configuration
TENANT_ID = "1485f8b4-04e9-47b7-ad8a-27adbe78d20a"
PLATFORM = "facebook"
PAGE_ID = "802786652928846"  # Krusty Pizza & Pasta

def get_access_token():
    """Get decrypted access token from database."""
    db = SessionLocal()
    try:
        token_service = TokenService()
        access_token = token_service.get_active_token(
            db=db,
            tenant_id=TENANT_ID,
            platform=PLATFORM
        )
        return access_token
    finally:
        db.close()

def post_to_facebook(access_token, message):
    """Post a message to Facebook Page."""
    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/feed"

    data = {
        "message": message,
        "access_token": access_token
    }

    response = requests.post(url, data=data)
    return response.json()

def main():
    print("🧪 Testing Facebook Post via Multi-Tenant OAuth System\n")
    print("=" * 60)

    # Step 1: Get decrypted token
    print("\n📝 Step 1: Retrieving decrypted access token from database...")
    try:
        access_token = get_access_token()
        print(f"✅ Token retrieved successfully (length: {len(access_token)} chars)")
        print(f"   Preview: {access_token[:20]}...")
    except Exception as e:
        print(f"❌ Error retrieving token: {e}")
        return

    # Step 2: Create test message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_message = f"""🧪 Test Post from Multi-Tenant OAuth System

This is a test post created at {timestamp} to verify that:
✅ OAuth2 authentication is working
✅ Tokens are properly encrypted and stored
✅ Token retrieval and decryption works
✅ Facebook Graph API integration is functional

Posted via our secure multi-tenant social media automation platform! 🚀

#TestPost #OAuth2 #Automation"""

    print(f"\n📝 Step 2: Creating test post...")
    print(f"   Message length: {len(test_message)} chars")

    # Step 3: Post to Facebook
    print(f"\n📤 Step 3: Posting to Facebook Page (ID: {PAGE_ID})...")
    try:
        result = post_to_facebook(access_token, test_message)

        if "id" in result:
            post_id = result["id"]
            print(f"\n✅ SUCCESS! Post created successfully!")
            print(f"   Post ID: {post_id}")
            print(f"   View at: https://www.facebook.com/{post_id.replace('_', '/posts/')}")
        elif "error" in result:
            error = result["error"]
            print(f"\n❌ ERROR: {error.get('message', 'Unknown error')}")
            print(f"   Error code: {error.get('code', 'N/A')}")
            print(f"   Error type: {error.get('type', 'N/A')}")
        else:
            print(f"\n❓ Unexpected response: {result}")
    except Exception as e:
        print(f"\n❌ Error posting to Facebook: {e}")
        return

    print("\n" + "=" * 60)
    print("✅ Test complete!\n")

if __name__ == "__main__":
    main()
