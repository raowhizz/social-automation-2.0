"""
Encryption service for securing OAuth tokens and sensitive data.
Uses AES-256-GCM for authenticated encryption.
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


class EncryptionService:
    """Service for encrypting and decrypting sensitive data like OAuth tokens."""

    def __init__(self, encryption_key: str = None):
        """
        Initialize encryption service with a key.

        Args:
            encryption_key: Base64-encoded 32-byte key. If None, reads from ENCRYPTION_KEY env var.

        Raises:
            ValueError: If encryption key is missing or invalid.
        """
        if encryption_key is None:
            encryption_key = os.getenv("ENCRYPTION_KEY")

        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable is required. "
                "Generate one with: python generate_keys.py"
            )

        try:
            # Decode the base64 key
            self.key = base64.b64decode(encryption_key)
            if len(self.key) != 32:
                raise ValueError("Encryption key must be exactly 32 bytes")

            # Initialize AES-GCM cipher
            self.cipher = AESGCM(self.key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted data in format: nonce||ciphertext

        Raises:
            ValueError: If plaintext is empty
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")

        # Generate a random 96-bit nonce (12 bytes is standard for GCM)
        nonce = os.urandom(12)

        # Encrypt the plaintext
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext = self.cipher.encrypt(nonce, plaintext_bytes, None)

        # Combine nonce + ciphertext and encode as base64
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_data: Base64-encoded encrypted data (nonce||ciphertext)

        Returns:
            The decrypted plaintext string

        Raises:
            ValueError: If decryption fails (invalid data or tampered ciphertext)
        """
        if not encrypted_data:
            raise ValueError("Cannot decrypt empty string")

        try:
            # Decode from base64
            data = base64.b64decode(encrypted_data)

            # Extract nonce (first 12 bytes) and ciphertext (rest)
            nonce = data[:12]
            ciphertext = data[12:]

            # Decrypt
            plaintext_bytes = self.cipher.decrypt(nonce, ciphertext, None)
            return plaintext_bytes.decode('utf-8')

        except InvalidTag:
            raise ValueError("Decryption failed: Data has been tampered with or key is incorrect")
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt all string values in a dictionary.

        Args:
            data: Dictionary with string values to encrypt

        Returns:
            Dictionary with encrypted string values
        """
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str) and value:
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = value
        return encrypted

    def decrypt_dict(self, data: dict) -> dict:
        """
        Decrypt all encrypted values in a dictionary.

        Args:
            data: Dictionary with encrypted string values

        Returns:
            Dictionary with decrypted string values
        """
        decrypted = {}
        for key, value in data.items():
            if isinstance(value, str) and value:
                try:
                    decrypted[key] = self.decrypt(value)
                except ValueError:
                    # If decryption fails, return as-is (might not be encrypted)
                    decrypted[key] = value
            else:
                decrypted[key] = value
        return decrypted


# Global encryption service instance
_encryption_service = None


def get_encryption_service() -> EncryptionService:
    """
    Get or create the global encryption service instance.

    Returns:
        EncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
