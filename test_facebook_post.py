#!/usr/bin/env python3
"""Quick test script to post to Facebook"""
import requests

PAGE_ID = "802786652928846"
ACCESS_TOKEN = "EAAJ5haRCYbABP7tFJKhVM9XUxteEkX3pC76vKhfp7CjKqBKZBYnkZBuMlz4JwYwtJ7AgGMox9hgnBLrTvjYAddxHgwwVQxfysf7jp3XBoCmLqlhEZBeREwUE9syUbDoFG6kiI1osZCjR6Wn16UvA5DwTZCGF1P3gyUzoZC68WZAw2tkOVrezZCaTwXlKZAhOWhZCTC3uKgjDiC9bkqsFaaaIsE9paFmLEGrZB0VBgdsh0UZD"

# Test text-only post
url = f"https://graph.facebook.com/v21.0/{PAGE_ID}/feed"

message = """🍕 Weekend Special at Krusty Pizza & Pasta!

Try our amazing Carnivore Pizza - loaded with beef salami, turkey ham, pepperoni, ground beef, Italian sausage, turkey bacon, and chicken!

Perfect for your weekend feast! Order now!

#KrustyPizza #WeekendSpecial #CarnivorePizza"""

data = {
    "message": message,
    "access_token": ACCESS_TOKEN
}

print("Attempting to post to Facebook...")
print(f"Page ID: {PAGE_ID}")
print(f"Message: {message[:100]}...")

response = requests.post(url, data=data)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ SUCCESS! Post ID: {result.get('id')}")
    print(f"View at: https://www.facebook.com/{result.get('id')}")
else:
    print(f"\n❌ FAILED")
