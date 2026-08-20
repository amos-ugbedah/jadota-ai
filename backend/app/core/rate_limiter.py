from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

# Create rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Rate limit configurations
RATE_LIMITS = {
    "auth": "5/minute",
    "trading": "30/minute",
    "api": "100/minute",
    "admin": "20/minute",
    "public": "60/minute",
}

def setup_rate_limiter(app: FastAPI):
    """Setup rate limiter for the app."""
    app.state.limiter = limiter
    logger.info("Rate limiter initialized")
