#!/usr/bin/env python
"""
Add missing columns to users table
Run: python add_missing_columns.py
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

def add_missing_columns():
    """Add missing columns to users table"""
    db = SessionLocal()
    
    try:
        # Get existing columns
        result = db.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Columns to add
        new_columns = [
            ("last_login_ip", "VARCHAR(45)"),
            ("real_balance", "FLOAT DEFAULT 0.0"),
            ("total_deposits", "FLOAT DEFAULT 0.0"),
            ("total_withdrawals", "FLOAT DEFAULT 0.0"),
            ("total_pnl", "FLOAT DEFAULT 0.0"),
            ("subscription_plan", "VARCHAR(50)"),
            ("subscription_expires_at", "DATETIME"),
            ("is_subscription_active", "BOOLEAN DEFAULT 0"),
            ("preferences", "TEXT"),
        ]
        
        added = []
        for col_name, col_type in new_columns:
            if col_name not in columns:
                try:
                    db.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    added.append(col_name)
                    logger.info(f"✅ Added column: {col_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to add {col_name}: {e}")
        
        db.commit()
        
        if added:
            logger.info(f"✅ Added columns: {', '.join(added)}")
        else:
            logger.info("✅ All columns already exist")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🛠️  Adding missing columns to users table")
    print("="*50)
    add_missing_columns()
    print("="*50)