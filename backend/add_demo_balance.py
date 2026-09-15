#!/usr/bin/env python
"""
Add demo_balance column to users table
Run: python add_demo_balance.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_demo_balance():
    """Add demo_balance column to users table"""
    db = SessionLocal()
    
    try:
        # Check if column exists
        result = db.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'demo_balance' in columns:
            logger.info("✅ demo_balance column already exists")
            return
        
        # Add the column
        logger.info("📝 Adding demo_balance column...")
        db.execute(text("ALTER TABLE users ADD COLUMN demo_balance FLOAT DEFAULT 10000.0"))
        db.commit()
        
        logger.info("✅ demo_balance column added successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error adding column: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🛠️  Adding demo_balance column to users table")
    print("="*50)
    add_demo_balance()
    print("="*50)
    print("✅ Done! You can now run create_admin.py")