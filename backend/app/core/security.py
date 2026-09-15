from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import hashlib
import hmac
import os
from .config import settings

# ============================================
# Password Hashing Context
# ============================================
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# ============================================
# Password Functions
# ============================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    if not password:
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
        errors.append("Password must contain at least one special character")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "strength": "strong" if len(errors) == 0 else "weak"
    }

# ============================================
# JWT Functions
# ============================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None

# ============================================
# 🔥 Token Header Extraction - ADDED
# ============================================
def get_token_from_header(authorization: str) -> Optional[str]:
    """
    Extract token from Authorization header.
    
    Args:
        authorization: The Authorization header value
        
    Returns:
        The extracted token or None
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]

def is_token_expired(token_data: dict) -> bool:
    """Check if a token has expired."""
    exp = token_data.get("exp")
    if not exp:
        return True
    
    if isinstance(exp, (int, float)):
        exp_dt = datetime.fromtimestamp(exp)
    else:
        exp_dt = exp
    
    return datetime.utcnow() > exp_dt

def get_token_remaining_time(token_data: dict) -> int:
    """Get remaining time in seconds for a token."""
    exp = token_data.get("exp")
    if not exp:
        return 0
    
    if isinstance(exp, (int, float)):
        exp_dt = datetime.fromtimestamp(exp)
    else:
        exp_dt = exp
    
    remaining = (exp_dt - datetime.utcnow()).total_seconds()
    return max(0, int(remaining))

# ============================================
# API Key Functions
# ============================================
def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hmac.compare_digest(hash_api_key(api_key), hashed_key)

# ============================================
# Token Generation Functions
# ============================================
def generate_verification_token() -> str:
    """Generate a verification token for email verification."""
    return secrets.token_urlsafe(32)

def generate_reset_token() -> str:
    """Generate a password reset token."""
    return secrets.token_urlsafe(32)

def generate_2fa_secret() -> str:
    """Generate a 2FA secret key."""
    try:
        import pyotp
        return pyotp.random_base32()
    except ImportError:
        return secrets.token_hex(20)

# ============================================
# Encryption/Decryption Functions
# ============================================
def encrypt_data(data: str, key: str = None) -> str:
    """Simple encryption for sensitive data."""
    if not data:
        return ""
    
    if not key:
        key = settings.encryption_key
    
    key_bytes = key.encode()
    data_bytes = data.encode()
    encrypted = bytes([data_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data_bytes))])
    return encrypted.hex()

def decrypt_data(encrypted_data: str, key: str = None) -> str:
    """Simple decryption for sensitive data."""
    if not encrypted_data:
        return ""
    
    if not key:
        key = settings.encryption_key
    
    encrypted_bytes = bytes.fromhex(encrypted_data)
    key_bytes = key.encode()
    decrypted = bytes([encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(encrypted_bytes))])
    return decrypted.decode()

# ============================================
# CSRF Token Generation
# ============================================
def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)

# ============================================
# Session ID Generation
# ============================================
def generate_session_id() -> str:
    """Generate a unique session ID."""
    return secrets.token_hex(32)

# ============================================
# Helper: Mask sensitive data
# ============================================
def mask_email(email: str) -> str:
    """Mask an email address for display."""
    if not email or '@' not in email:
        return email
    
    parts = email.split('@')
    username, domain = parts[0], parts[1]
    
    if len(username) <= 2:
        masked_username = username[0] + '***'
    else:
        masked_username = username[0] + '***' + username[-1]
    
    return f"{masked_username}@{domain}"

def mask_api_key(api_key: str) -> str:
    """Mask an API key for display."""
    if not api_key:
        return ""
    
    if len(api_key) <= 8:
        return "***"
    
    return api_key[:4] + "***" + api_key[-4:]

# ============================================
# Session Management
# ============================================
def create_session_id(user_id: str) -> str:
    """Create a session ID for a user."""
    timestamp = datetime.utcnow().isoformat()
    return secrets.token_hex(16) + f"_{user_id}_{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"