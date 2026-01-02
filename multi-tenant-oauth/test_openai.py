#!/usr/bin/env python
"""Test OpenAI integration for content generation."""

import requests
import json

# Test caption generation API
url = "http://localhost:8000/api/v1/posts/generate"
data = {
    "tenant_id": "1485f8b4-04e9-47b7-ad8a-27adbe78d20a",
    "restaurant_name": "Krusty Pizza & Pasta",
    "restaurant_description": "Family-owned Italian restaurant serving authentic pizza and pasta",
    "post_type": "daily_special",
    "item_name": "Margherita Pizza",
    "item_description": "Fresh mozzarella, basil, and tomato sauce",
    "tone": "friendly",
    "platform": "facebook"
}

print("=== Testing OpenAI Content Generation ===\n")
print("Sending request to:", url)

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        result = response.json()
        caption = result.get("caption", "")

        print("Generated Caption:")
        print("-" * 60)
        print(caption)
        print("-" * 60)

        # Analyze if it's template or AI
        template_indicators = [
            "Our chef's creation",
            "Freshly prepared with love",
            "Today's special"
        ]

        is_template = any(indicator in caption for indicator in template_indicators)

        print("\nAnalysis:")
        if is_template:
            print("⚠️  This appears to be a TEMPLATE-BASED caption")
            print("    (OpenAI API may not be configured or an error occurred)")
        else:
            print("✅ This appears to be an AI-GENERATED caption")
            print("    (OpenAI API is working!)")

    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Error: {e}")
