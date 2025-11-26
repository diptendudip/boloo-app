#!/usr/bin/env python3
"""
Azure Database Schema Fix for 4-Level Import
Fixes the schema to support all 4 levels: States, Districts, Blocks, Panchayats
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment"""
    db_url = os.environ.get('DATABASE_URL')

    if not db_url or not db_url.startswith('postgresql'):
        logger.error("Please set DATABASE_URL environment variable")
        return None

    if '@' in db_url:
        masked_url = db_url.split('@')[1]
        logger.info(f"Database: {masked_url}")

    return db_url


def fix_districts_schema(db):
    """Fix admin_districts table to add unique constraint on lgd_code"""
    logger.info("Step 1: Fixing admin_districts schema...")

    # Make lgd_code NOT NULL and add UNIQUE constraint
    try:
        # First, set default values for any NULL lgd_codes
        logger.info("  - Setting default values for NULL lgd_codes...")
        update_nulls = text("""
            UPDATE admin_districts
            SET lgd_code = CONCAT('DIST_', id)
            WHERE lgd_code IS NULL OR lgd_code = '';
        """)
        result = db.execute(update_nulls)
        db.commit()
        logger.info(f"  - Updated {result.rowcount} rows")

        # Make column NOT NULL
        logger.info("  - Making lgd_code NOT NULL...")
        alter_not_null = text("""
            ALTER TABLE admin_districts
            ALTER COLUMN lgd_code SET NOT NULL;
        """)
        db.execute(alter_not_null)
        db.commit()

        # Add UNIQUE constraint
        logger.info("  - Adding UNIQUE constraint...")
        add_unique = text("""
            ALTER TABLE admin_districts
            ADD CONSTRAINT admin_districts_lgd_code_unique UNIQUE (lgd_code);
        """)
        db.execute(add_unique)
        db.commit()

        logger.info("  ✓ admin_districts schema fixed")

    except Exception as e:
        logger.error(f"  ✗ Failed to fix districts schema: {e}")
        raise


def create_blocks_table(db):
    """Create admin_blocks table"""
    logger.info("Step 2: Creating admin_blocks table...")

    create_blocks = text("""
        CREATE TABLE IF NOT EXISTS admin_blocks (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            name_en VARCHAR(255) NOT NULL,
            lgd_code VARCHAR(10) NOT NULL UNIQUE,
            district_lgd_code VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (district_lgd_code) REFERENCES admin_districts(lgd_code) ON DELETE CASCADE
        );
    """)
    db.execute(create_blocks)
    db.commit()

    # Create indexes
    create_block_indexes = text("""
        CREATE INDEX IF NOT EXISTS idx_blocks_district_code ON admin_blocks(district_lgd_code);
        CREATE INDEX IF NOT EXISTS idx_blocks_lgd_code ON admin_blocks(lgd_code);
    """)
    db.execute(create_block_indexes)
    db.commit()

    logger.info("  ✓ admin_blocks table created")


def create_panchayats_table(db):
    """Create admin_panchayats table"""
    logger.info("Step 3: Creating admin_panchayats table...")

    create_panchayats = text("""
        CREATE TABLE IF NOT EXISTS admin_panchayats (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            name_en VARCHAR(255) NOT NULL,
            lgd_code VARCHAR(10) NOT NULL UNIQUE,
            block_lgd_code VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (block_lgd_code) REFERENCES admin_blocks(lgd_code) ON DELETE CASCADE
        );
    """)
    db.execute(create_panchayats)
    db.commit()

    # Create indexes
    create_panchayat_indexes = text("""
        CREATE INDEX IF NOT EXISTS idx_panchayats_block_code ON admin_panchayats(block_lgd_code);
        CREATE INDEX IF NOT EXISTS idx_panchayats_lgd_code ON admin_panchayats(lgd_code);
    """)
    db.execute(create_panchayat_indexes)
    db.commit()

    logger.info("  ✓ admin_panchayats table created")


def verify_schema(db):
    """Verify all 4 tables exist with correct schema"""
    logger.info("\nVerifying schema...")

    tables = ['admin_states', 'admin_districts', 'admin_blocks', 'admin_panchayats']

    for table in tables:
        count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        logger.info(f"  ✓ {table}: {count} rows")

    logger.info("\nAll 4 tables verified successfully!")


def main():
    logger.info("=" * 80)
    logger.info("AZURE DATABASE SCHEMA FIX FOR 4-LEVEL IMPORT")
    logger.info("=" * 80)

    db_url = get_database_url()
    if not db_url:
        return False

    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={
                'connect_timeout': 30,
                'options': '-c statement_timeout=300000'
            }
        )

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        logger.info("✓ Database connection established\n")

        # Fix schema
        fix_districts_schema(db)
        create_blocks_table(db)
        create_panchayats_table(db)

        # Verify
        verify_schema(db)

        logger.info("\n" + "=" * 80)
        logger.info("✓ SCHEMA FIX COMPLETE!")
        logger.info("  Now run: python3 scripts/import_all_4_levels_azure.py")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Schema fix failed: {e}", exc_info=True)
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
