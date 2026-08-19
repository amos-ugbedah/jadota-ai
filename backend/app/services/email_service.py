import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer
from ..core.config import settings

# Create serializer for tokens
serializer = URLSafeTimedSerializer(settings.secret_key)

def generate_verification_token(email: str) -> str:
    """Generate a verification token for email."""
    return serializer.dumps(email, salt="email-verification")

def generate_reset_token(email: str) -> str:
    """Generate a password reset token."""
    return serializer.dumps(email, salt="password-reset")

def verify_token(token: str, salt: str, max_age: int = 3600) -> str:
    """Verify a token and return the email."""
    try:
        email = serializer.loads(token, salt=salt, max_age=max_age)
        return email
    except Exception:
        return None

def send_verification_email(email: str, username: str, token: str):
    """Send email verification email."""
    # For development, print the verification link
    verification_url = f"{settings.frontend_url}/verify-email?token={token}"
    
    print("=" * 60)
    print(f"📧 VERIFICATION EMAIL (Development Mode)")
    print(f"To: {email}")
    print(f"Subject: Verify your JADOTA AI account")
    print(f"\nHi {username},")
    print(f"\nPlease verify your email by clicking the link below:")
    print(f"\n{verification_url}")
    print(f"\nThis link will expire in 1 hour.")
    print("=" * 60)
    
    # Uncomment below for production with SendGrid
    """
    message = Mail(
        from_email='noreply@jadota.ai',
        to_emails=email,
        subject='Verify your JADOTA AI account',
        html_content=f'''
        <h1>Welcome to JADOTA AI!</h1>
        <p>Hi {username},</p>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href="{verification_url}">Verify Email</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't create an account, please ignore this email.</p>
        '''
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"Email sent to {email}, status: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")
    """

def send_password_reset_email(email: str, username: str, token: str):
    """Send password reset email."""
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    
    print("=" * 60)
    print(f"🔑 PASSWORD RESET EMAIL (Development Mode)")
    print(f"To: {email}")
    print(f"Subject: Reset your JADOTA AI password")
    print(f"\nHi {username},")
    print(f"\nYou requested to reset your password. Click the link below:")
    print(f"\n{reset_url}")
    print(f"\nThis link will expire in 1 hour.")
    print(f"\nIf you didn't request this, please ignore this email.")
    print("=" * 60)
    
    # Uncomment below for production with SendGrid
    """
    message = Mail(
        from_email='noreply@jadota.ai',
        to_emails=email,
        subject='Reset your JADOTA AI password',
        html_content=f'''
        <h1>Reset Your Password</h1>
        <p>Hi {username},</p>
        <p>You requested to reset your password. Click the link below:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
        '''
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"Password reset email sent to {email}, status: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")
    """
