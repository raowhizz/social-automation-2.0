#!/usr/bin/env python3
"""Quick test of OpenAI API key."""

import os
import sys

# Read API key from .env
with open('.env') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            api_key = line.split('=', 1)[1].strip()
            break

print("API Key from .env:")
print(f"  Prefix: {api_key[:10]}...")
print(f"  Suffix: ...{api_key[-10:]}")
print(f"  Length: {len(api_key)} characters")

# Try to test the API
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    print("\n✓ OpenAI client initialized")
    print("\nTesting API call...")

    # Make a simple test call
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Say 'API works!'"}],
        max_tokens=10
    )

    print("✅ SUCCESS! OpenAI API is working!")
    print(f"Response: {response.choices[0].message.content}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nThis suggests:")
    print("  1. The API key in .env may be invalid or revoked")
    print("  2. OpenAI account may be out of credits")
    print("  3. Network connectivity issue")
