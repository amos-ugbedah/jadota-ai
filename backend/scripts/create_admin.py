#!/usr/bin/env python
"""
Create Admin User Script

Usage:
    python scripts/create_admin.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin():
    db = SessionLocal()
    
    try:
        # Your admin details
        email = "ugbedahamos@gmail.com"
        password = "Jason&Jaden"
        full_name = "Ugbedah Amos"
        
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"⚠️ User {email} already exists!")
            print(f"   Current Role: {existing.role}")
            print(f"   Updating to SUPER_ADMIN...")
            
            existing.role = "SUPER_ADMIN"
            existing.is_verified = True
            existing.is_active = True
            existing.full_name = full_name
            db.commit()
            db.refresh(existing)
            
            print("\n" + "="*60)
            print("✅ USER UPDATED TO SUPER_ADMIN!")
            print("="*60)
            print(f"   Email:    {existing.email}")
            print(f"   Name:     {existing.full_name}")
            print(f"   Role:     {existing.role}")
            print(f"   ID:       {existing.id}")
            print("="*60)
            print("\n🔐 Login at: http://localhost:3000/login")
            print(f"   Email: {existing.email}")
            print(f"   Password: Jason&Jaden")
            print("="*60)
            return
        
        # Create new user
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role="SUPER_ADMIN",
            is_verified=True,
            is_active=True,
            demo_balance=100000,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("\n" + "="*60)
        print("✅ ADMIN USER CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"   Email:    {user.email}")
        print(f"   Name:     {user.full_name}")
        print(f"   Role:     {user.role}")
        print(f"   ID:       {user.id}")
        print(f"   Balance:  ${user.demo_balance}")
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
    create_admin()