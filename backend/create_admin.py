#!/usr/bin/env python
"""
Create Admin User - Quick Script
Run: python create_admin.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash

def create_admin():
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Your admin details
        email = "ugbedahamos@gmail.com"
        password = "Jason&Jaden"
        full_name = "Ugbedah Amos"
        username = "ugbedahamos"
        
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"⚠️ User {email} already exists!")
            print(f"   Current Role: {existing.role}")
            print(f"   Updating to SUPER_ADMIN...")
            
            # Update existing user to SUPER_ADMIN
            existing.role = "SUPER_ADMIN"
            existing.is_verified = True
            existing.is_active = True
            existing.full_name = full_name
            existing.username = username
            existing.demo_balance = 100000.0
            existing.subscription_plan = "ENTERPRISE"
            existing.is_subscription_active = True
            from datetime import datetime, timedelta
            existing.subscription_expires_at = datetime.utcnow() + timedelta(days=365)
            
            db.commit()
            db.refresh(existing)
            
            print("\n" + "="*60)
            print("✅ USER UPDATED TO SUPER_ADMIN!")
            print("="*60)
            print(f"   Email:    {existing.email}")
            print(f"   Name:     {existing.full_name}")
            print(f"   Username: {existing.username}")
            print(f"   Role:     {existing.role}")
            print(f"   ID:       {existing.id}")
            print(f"   Demo Bal: ${existing.demo_balance:,.2f}")
            print(f"   Plan:     {existing.subscription_plan}")
            print("="*60)
            print("\n🔐 Login at: http://localhost:3000/login")
            print(f"   Email: {existing.email}")
            print(f"   Password: Jason&Jaden")
            print("="*60)
            return
        
        # Create new user with SUPER_ADMIN role
        from datetime import datetime, timedelta
        
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role="SUPER_ADMIN",
            is_verified=True,
            is_active=True,
            demo_balance=100000.0,
            subscription_plan="ENTERPRISE",
            is_subscription_active=True,
            subscription_expires_at=datetime.utcnow() + timedelta(days=365),
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("\n" + "="*60)
        print("✅ ADMIN USER CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"   Email:    {user.email}")
        print(f"   Name:     {user.full_name}")
        print(f"   Username: {user.username}")
        print(f"   Role:     {user.role}")
        print(f"   ID:       {user.id}")
        print(f"   Demo Bal: ${user.demo_balance:,.2f}")
        print(f"   Plan:     {user.subscription_plan}")
        print("="*60)
        print("\n🔐 Login at: http://localhost:3000/login")
        print(f"   Email: {user.email}")
        print(f"   Password: Jason&Jaden")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🛠️  JADOTA AI - Admin User Creator")
    print("="*60)
    print("Creating admin with details:")
    print(f"   Email: ugbedahamos@gmail.com")
    print(f"   Name: Ugbedah Amos")
    print(f"   Username: ugbedahamos")
    print(f"   Role: SUPER_ADMIN")
    print("="*60)
    create_admin()