#!/usr/bin/env python3
"""
Key Generation Script for Multi-Tenant OAuth System
Generates secure SECRET_KEY and ENCRYPTION_KEY for .env file
"""

import secrets
import base64
import os


def generate_secret_key():
    """Generate a secure SECRET_KEY for JWT and session management."""
    return secrets.token_urlsafe(32)


def generate_encryption_key():
    """Generate a 32-byte AES-256 encryption key (base64-encoded)."""
    # Generate 32 random bytes
    key_bytes = os.urandom(32)
    # Encode as base64 for storage in .env
    return base64.b64encode(key_bytes).decode('utf-8')


def main():
    print("=" * 60)
    print("Multi-Tenant OAuth - Security Key Generator")
    print("=" * 60)
    print()

    # Generate keys
    secret_key = generate_secret_key()
    encryption_key = generate_encryption_key()

    print("🔑 Generated Security Keys:")
    print()
    print("Copy these values to your .env file:")
    print("-" * 60)
    print()
    print(f"SECRET_KEY={secret_key}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print()
    print("-" * 60)
    print()
    print("✅ Keys generated successfully!")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Keep these keys secret (never commit to git)")
    print("   - Use different keys for development and production")
    print("   - Store production keys in secure secret management")
    print("   - ENCRYPTION_KEY is 32 bytes (AES-256 compatible)")
    print()
    print("📝 Next steps:")
    print("   1. Open your .env file")
    print("   2. Replace SECRET_KEY and ENCRYPTION_KEY with values above")
    print("   3. Save the file")
    print("   4. Continue with environment configuration")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
