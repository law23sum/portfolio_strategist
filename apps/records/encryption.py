"""
Encryption utilities for sensitive financial data (access tokens, API keys, etc.)
"""

import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet
from django.conf import settings

logger = logging.getLogger(__name__)


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key from settings.
    If not set, generates a key (should be set in production).
    """
    key = getattr(settings, 'FERNET_KEY', None)
    if not key:
        logger.warning("FERNET_KEY not set in settings. Generating a new key (not suitable for production).")
        key = Fernet.generate_key().decode()
    elif isinstance(key, str):
        key = key.encode()
    return key


def encrypt_token(token: str) -> str:
    """
    Encrypt a token (access token, API key, etc.) for storage.
    Returns base64-encoded encrypted string.
    """
    try:
        key = get_encryption_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(token.encode())
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Error encrypting token: {e}")
        raise


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a token from storage.
    Returns the original token string.
    """
    try:
        key = get_encryption_key()
        cipher = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_token.encode())
        decrypted = cipher.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting token: {e}")
        raise



