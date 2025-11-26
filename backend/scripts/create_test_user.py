#!/usr/bin/env python3
"""
Create test user for OTP testing (OTP: 123456)
This user ID matches the dummy user in mobile app's AuthContext
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import UUID
from datetime import datetime

from app.config import settings
from app.models.user import User

def create_test_user():
    """Create or update test user in database"""

    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        test_user_id = UUID('11111111-1111-1111-1111-111111111111')

        # Check if user already exists
        existing_user = db.query(User).filter(User.id == test_user_id).first()

        if existing_user:
            print(f"Test user already exists: {existing_user.phone}")
            print(f"  ID: {existing_user.id}")
            print(f"  Name: {existing_user.name}")
            print(f"  Training Mode: {existing_user.training_mode_enabled}")
            print(f"  Training Reports: {existing_user.training_reports_count}")
            print(f"  Training Completed: {existing_user.training_completed}")

            # Update training fields to ensure they're set correctly
            existing_user.training_mode_enabled = True
            existing_user.training_reports_count = 0
            existing_user.training_completed = False
            db.commit()
            print("\n✅ Updated training mode settings for test user")

        else:
            # Create new test user
            test_user = User(
                id=test_user_id,
                phone='+919999999999',
                email='test@boloo.app',  # Required field
                name='Test User',
                role='citizen',
                training_reports_count=0,
                training_completed=False,
                training_mode_enabled=True,
                created_at=datetime.utcnow()
            )

            db.add(test_user)
            db.commit()
            db.refresh(test_user)

            print("✅ Created test user successfully!")
            print(f"  ID: {test_user.id}")
            print(f"  Phone: {test_user.phone}")
            print(f"  Name: {test_user.name}")
            print(f"  Training Mode: {test_user.training_mode_enabled}")
            print(f"  Training Reports: {test_user.training_reports_count}")

        print("\n📱 You can now login in the mobile app with:")
        print("   Phone: any number")
        print("   OTP: 123456")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
