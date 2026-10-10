"""
Symmetric encryption for secrets at rest (exchange API keys).

Uses Fernet (AES-128-CBC + HMAC-SHA256) with a key derived from
settings.encryption_key. Rotating the key requires re-encrypting all
stored values — change it carefully.
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from ..core.config import settings

logger = logging.getLogger(__name__)


def _derive_fernet_key(raw: str) -> bytes:
    """Turn an arbitrary-length secret into a valid Fernet key."""
    if not raw:
        raise ValueError("ENCRYPTION_KEY is not set — cannot encrypt credentials")
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = _derive_fernet_key(settings.encryption_key)
        _fernet = Fernet(key)
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns urlsafe base64 ciphertext."""
    if not plaintext:
        return ""
    token = _get_fernet().encrypt(plaintext.encode("utf-8"))
    return token.decode("ascii")


def decrypt(ciphertext: str) -> str:
    """
    Decrypt a ciphertext produced by encrypt(). Returns "" on failure
    so a bad key doesn't crash every request that touches credentials.
    """
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, Exception) as e:
        logger.error(f"Failed to decrypt credential: {type(e).__name__}")
        return ""


def mask(secret: str, visible: int = 4) -> str:
    """Show only the first N chars; safe for logging."""
    if not secret:
        return ""
    if len(secret) <= visible:
        return "***"
    return secret[:visible] + "***" + secret[-2:]