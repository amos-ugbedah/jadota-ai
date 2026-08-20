from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, HTTPException, status
import time

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "auth": "5/minute",  # Login/register attempts
    "trading": "30/minute",  # Trade requests
    "api": "100/minute",  # General API calls
    "admin": "20/minute",  # Admin endpoints
    "public": "60/minute",  # Public endpoints
}

class RateLimiter:
    """Custom rate limiter with different limits for different endpoints."""
    
    @staticmethod
    def get_limiter(limit: str):
        """Get a rate limiter for a specific limit."""
        return limiter.limit(limit)
    
    @staticmethod
    def auth_limiter():
        """Rate limiter for authentication endpoints."""
        return limiter.limit(RATE_LIMITS["auth"])
    
    @staticmethod
    def trading_limiter():
        """Rate limiter for trading endpoints."""
        return limiter.limit(RATE_LIMITS["trading"])
    
    @staticmethod
    def admin_limiter():
        """Rate limiter for admin endpoints."""
        return limiter.limit(RATE_LIMITS["admin"])
    
    @staticmethod
    def public_limiter():
        """Rate limiter for public endpoints."""
        return limiter.limit(RATE_LIMITS["public"])

# Create middleware
rate_limit_middleware = SlowAPIMiddleware
