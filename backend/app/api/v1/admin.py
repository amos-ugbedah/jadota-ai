from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...schemas.admin import (
    DashboardStats, UserListItem, UserDetailResponse,
    UserUpdateRequest, AdminActionResponse,
    SystemLogResponse, SystemMetricResponse
)
from ...services.admin_service import admin_service
from ...api.dependencies import get_current_user, get_admin_user
from ...models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get dashboard statistics."""
    return admin_service.get_dashboard_stats(db)

@router.get("/users", response_model=List[UserListItem])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get list of users."""
    return admin_service.get_users(db, skip, limit, search)

@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get detailed user information."""
    try:
        return admin_service.get_user_detail(db, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Update user information."""
    try:
        user = admin_service.update_user(
            db, user_id, update_data.dict(exclude_unset=True)
        )
        
        # Log action
        admin_service.log_admin_action(
            db,
            current_user.id,
            "UPDATE_USER",
            "user",
            user_id,
            update_data.dict(exclude_unset=True)
        )
        
        return {'message': 'User updated successfully', 'user_id': user_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Suspend a user."""
    try:
        admin_service.update_user(db, user_id, {'is_active': False})
        admin_service.log_admin_action(
            db,
            current_user.id,
            "SUSPEND_USER",
            "user",
            user_id
        )
        return {'message': 'User suspended successfully'}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/users/{user_id}/restore")
async def restore_user(
    user_id: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Restore a suspended user."""
    try:
        admin_service.update_user(db, user_id, {'is_active': True})
        admin_service.log_admin_action(
            db,
            current_user.id,
            "RESTORE_USER",
            "user",
            user_id
        )
        return {'message': 'User restored successfully'}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/logs", response_model=List[SystemLogResponse])
async def get_system_logs(
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get system logs."""
    logs = admin_service.get_system_logs(db, limit)
    return logs

@router.get("/metrics", response_model=List[dict])
async def get_system_metrics(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get system metrics."""
    return admin_service.get_system_metrics(db, hours)

@router.get("/actions", response_model=List[AdminActionResponse])
async def get_admin_actions(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get recent admin actions."""
    actions = admin_service.get_admin_actions(db, limit)
    
    # Add admin email to response
    result = []
    for action in actions:
        admin = db.query(User).filter(User.id == action.admin_id).first()
        result.append({
            **action.__dict__,
            'admin_email': admin.email if admin else None
        })
    
    return result
