"""Test script for post suggestions."""

import requests
import json

# Configuration
API_URL = "http://localhost:8000"
TENANT_ID = "1485f8b4-04e9-47b7-ad8a-27adbe78d20a"  # Krusty Pizza tenant


def test_suggestions():
    """Test post suggestions endpoint."""
    print("=" * 80)
    print("TESTING POST SUGGESTIONS")
    print("=" * 80)

    url = f"{API_URL}/api/v1/restaurant/{TENANT_ID}/suggestions?count=5"
    response = requests.post(url)

    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        result = response.json()
        print("✅ Successfully generated post suggestions!\n")

        suggestions = result.get('suggestions', [])
        print(f"Total Suggestions: {len(suggestions)}\n")

        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{'='*80}")
            print(f"SUGGESTION #{i}: {suggestion.get('title')}")
            print(f"{'='*80}")
            print(f"Type: {suggestion.get('type')}")
            print(f"Target Day: {suggestion.get('target_day')}")
            print(f"Recommended Time: {suggestion.get('recommended_time')}")
            print(f"\nPost Text:")
            print(f"{suggestion.get('post_text')}")
            print(f"\nReason:")
            print(f"{suggestion.get('reason')}")

            if suggestion.get('featured_items'):
                print(f"\nFeatured Items: {', '.join(suggestion.get('featured_items'))}")

            if suggestion.get('hashtags'):
                print(f"\nHashtags: {' '.join(suggestion.get('hashtags'))}")

            print(f"\nCall to Action: {suggestion.get('call_to_action')}")

        # Print full JSON
        print("\n\n" + "=" * 80)
        print("FULL JSON RESPONSE:")
        print("=" * 80)
        print(json.dumps(result, indent=2))

    else:
        print(f"❌ Error: {response.text}")


if __name__ == "__main__":
    test_suggestions()
