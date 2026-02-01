"""Cryptographic utilities for Veritas database encryption.

This module provides encryption and decryption functions for sensitive data
stored in the database, specifically for private keys.
"""

import os
import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Default encryption key for development (DO NOT USE IN PRODUCTION)
# In production, always set ENCRYPTION_KEY environment variable
DEFAULT_ENCRYPTION_KEY = "veritas-default-encryption-key-do-not-use-in-production-32bytes"


def derive_fernet_key(key_material: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Derive a Fernet-compatible key from arbitrary key material.

    Fernet requires a 32-byte base64-encoded key. This function uses PBKDF2
    to derive a secure key from the provided key material.

    Args:
        key_material: The raw key material (e.g., from environment variable)
        salt: Optional salt bytes. If None, a default salt is used.

    Returns:
        Tuple of (fernet_key, salt) where fernet_key is base64-encoded
    """
    if salt is None:
        # Use a fixed salt for deterministic key derivation
        # In production, you might want to store salt with encrypted data
        salt = b"veritas_salt_fixed_v1"

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(key_material.encode()))
    return key, salt


def get_encryption_key() -> bytes:
    """Get the encryption key from environment or use default.

    Returns:
        Base64-encoded Fernet key ready for use

    Raises:
        ValueError: If key derivation fails
    """
    # Import settings here to avoid circular imports at module level
    from .config import settings

    key_material = settings.ENCRYPTION_KEY or os.getenv("ENCRYPTION_KEY", DEFAULT_ENCRYPTION_KEY)

    if key_material == DEFAULT_ENCRYPTION_KEY:
        logger.warning(
            "Using default encryption key. Set ENCRYPTION_KEY environment variable "
            "for production use."
        )

    fernet_key, _ = derive_fernet_key(key_material)
    return fernet_key


# Initialize Fernet cipher with the derived key
_fernet: Optional[Fernet] = None


def get_fernet() -> Fernet:
    """Get or initialize the Fernet cipher instance.

    Returns:
        Fernet cipher instance
    """
    global _fernet
    if _fernet is None:
        _fernet = Fernet(get_encryption_key())
    return _fernet


def encrypt_private_key(private_key: Optional[str]) -> Optional[str]:
    """Encrypt a private key for database storage.

    Args:
        private_key: The plaintext private key to encrypt

    Returns:
        Base64-encoded encrypted string, or None if input is None
    """
    if private_key is None:
        return None

    if not isinstance(private_key, str):
        raise TypeError("private_key must be a string")

    try:
        fernet = get_fernet()
        encrypted_bytes = fernet.encrypt(private_key.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to encrypt private key: {e}")
        raise


def decrypt_private_key(encrypted_key: Optional[str]) -> Optional[str]:
    """Decrypt a private key from database storage.

    Args:
        encrypted_key: The base64-encoded encrypted private key

    Returns:
        Decrypted plaintext private key, or None if input is None or decryption fails
    """
    if encrypted_key is None:
        return None

    if not isinstance(encrypted_key, str):
        logger.warning(f"encrypted_key must be a string, got {type(encrypted_key)}")
        return None

    try:
        fernet = get_fernet()
        decrypted_bytes = fernet.decrypt(encrypted_key.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        logger.warning("Failed to decrypt private key: Invalid token (wrong key or corrupted data)")
        return None
    except Exception as e:
        logger.warning(f"Failed to decrypt private key: {e}")
        return None


def rotate_encryption_key(encrypted_data: str, old_key_material: str, new_key_material: str) -> str:
    """Re-encrypt data with a new encryption key.

    Args:
        encrypted_data: The current encrypted data
        old_key_material: The current key material used for encryption
        new_key_material: The new key material to use

    Returns:
        Re-encrypted data with the new key
    """
    # Derive old key and decrypt
    old_key, _ = derive_fernet_key(old_key_material)
    old_fernet = Fernet(old_key)
    decrypted = old_fernet.decrypt(encrypted_data.encode("utf-8"))

    # Derive new key and encrypt
    new_key, _ = derive_fernet_key(new_key_material)
    new_fernet = Fernet(new_key)
    encrypted = new_fernet.encrypt(decrypted)

    return encrypted.decode("utf-8")


def generate_secure_key() -> str:
    """Generate a new secure encryption key.

    Returns:
        A secure random key suitable for ENCRYPTION_KEY environment variable
    """
    return Fernet.generate_key().decode("utf-8")
