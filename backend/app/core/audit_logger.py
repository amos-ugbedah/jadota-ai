import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request
from sqlalchemy.orm import Session

from ..models.risk import RiskEvent
from ..models.admin import SystemLog

logger = logging.getLogger(__name__)

class AuditLogger:
    """Audit logging for all system actions."""
    
    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ):
        """Log an action to the audit log."""
        log_entry = SystemLog(
            level="INFO",
            component="AUDIT",
            message=f"{action} on {resource_type}",
            details={
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details or {},
                'ip_address': ip_address,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        db.add(log_entry)
        db.commit()
        
        # Also log to standard logger
        logger.info(f"AUDIT: {action} on {resource_type} by user {user_id}")
    
    @staticmethod
    def log_security_event(
        db: Session,
        user_id: Optional[str],
        event_type: str,
        description: str,
        ip_address: Optional[str] = None,
        severity: str = "WARNING"
    ):
        """Log a security event."""
        log_entry = SystemLog(
            level=severity,
            component="SECURITY",
            message=f"{event_type}: {description}",
            details={
                'user_id': user_id,
                'event_type': event_type,
                'ip_address': ip_address,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        db.add(log_entry)
        db.commit()
        
        logger.warning(f"SECURITY: {event_type} - {description}")

def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
