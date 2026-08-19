from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import create_access_token, create_refresh_token
from ...schemas.user import UserCreate, UserLogin, UserResponse, Token
from ...services.user_service import UserService
from ...services.email_service import (
    generate_verification_token, 
    generate_reset_token,
    verify_token,
    send_verification_email,
    send_password_reset_email
)
from ...api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    try:
        user = UserService.create_user(db, user_data)
        
        # Generate verification token and send email
        token = generate_verification_token(user.email)
        send_verification_email(user.email, user.username, token)
        
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/verify-email")
async def verify_email(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Verify user's email address."""
    email = verify_token(token, "email-verification")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    
    user = UserService.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    UserService.verify_user_email(db, user.id)
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(
    email: str,
    db: Session = Depends(get_db),
):
    """Resend verification email."""
    user = UserService.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    token = generate_verification_token(user.email)
    send_verification_email(user.email, user.username, token)
    return {"message": "Verification email sent"}

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Login and get JWT tokens."""
    user = UserService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    UserService.update_last_login(db, user.id)
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: Session = Depends(get_db),
):
    """Send password reset email."""
    user = UserService.get_user_by_email(db, email)
    if not user:
        # Don't reveal if user exists or not
        return {"message": "If your email is registered, you will receive a reset link"}
    
    token = generate_reset_token(user.email)
    send_password_reset_email(user.email, user.username, token)
    return {"message": "If your email is registered, you will receive a reset link"}

@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db),
):
    """Reset password with token."""
    email = verify_token(token, "password-reset")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    user = UserService.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    UserService.update_password(db, user.id, new_password)
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user = Depends(get_current_user),
):
    """Get current user profile."""
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db),
):
    """Refresh access token."""
    from ...core.security import decode_token
    
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user = UserService.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
):
    """Logout user (client-side token removal)."""
    return {"message": "Successfully logged out"}
