from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...schemas.notification import (
    NotificationResponse, NotificationPreferenceResponse,
    UpdateNotificationPreference, MarkNotificationsRead,
    CreateNotificationRequest
)
from ...services.notification_service import notification_service
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = 50,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's notifications."""
    notifications = notification_service.get_user_notifications(
        db, current_user.id, limit, unread_only
    )
    return notifications

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get unread notification count."""
    count = notification_service.get_unread_count(db, current_user.id)
    return {"count": count}

@router.post("/mark-read")
async def mark_notifications_read(
    request: MarkNotificationsRead,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark notifications as read."""
    count = notification_service.mark_as_read(
        db, current_user.id, request.notification_ids
    )
    return {"message": f"Marked {count} notifications as read"}

@router.post("/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    count = notification_service.mark_all_as_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read"}

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notification preferences."""
    prefs = notification_service.get_preferences(db, current_user.id)
    return prefs

@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    updates: UpdateNotificationPreference,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences."""
    prefs = notification_service.update_preferences(
        db, current_user.id, updates.dict(exclude_unset=True)
    )
    return prefs

@router.post("/test")
async def send_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a test notification."""
    notification = notification_service.create_notification(
        db,
        current_user.id,
        "SYSTEM",
        "Test Notification",
        "This is a test notification from JADOTA AI",
        {"test": True}
    )
    return {"message": "Test notification sent", "notification_id": notification.id}
