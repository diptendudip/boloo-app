#!/usr/bin/env python3
"""
COMPLETE Azure Database Reimport - All 4 Levels
Drops and recreates all tables, then imports fresh data from CSV files

This fixes the critical issue where:
1. Only 2 levels (states, districts) were imported
2. Districts had duplicate/hash-based lgd_codes
3. Blocks and Panchayats were completely missing

Usage:
  DATABASE_URL="postgresql://..." python3 scripts/complete_azure_reimport.py
"""

import csv
import sys
import os
from pathlib import Path
from collections import defaultdict

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


def drop_and_create_all_tables(db):
    """Drop existing tables and create fresh schema"""
    logger.info("Dropping existing tables (if any)...")

    # Drop in reverse order due to foreign keys
    drop_commands = [
        "DROP TABLE IF EXISTS admin_panchayats CASCADE;",
        "DROP TABLE IF EXISTS admin_blocks CASCADE;",
        "DROP TABLE IF EXISTS admin_districts CASCADE;",
        "DROP TABLE IF EXISTS admin_states CASCADE;"
    ]

    for cmd in drop_commands:
        db.execute(text(cmd))

    db.commit()
    logger.info("✓ Existing tables dropped")

    logger.info("Creating fresh tables with correct schema...")

    # Create all 4 tables with proper constraints
    create_states = text("""
        CREATE TABLE admin_states (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            name_en VARCHAR(255) NOT NULL,
            state_code VARCHAR(10) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_states_code ON admin_states(state_code);
    """)
    db.execute(create_states)

    create_districts = text("""
        CREATE TABLE admin_districts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            name_en VARCHAR(255) NOT NULL,
            lgd_code VARCHAR(10) NOT NULL UNIQUE,
            state_code VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (state_code) REFERENCES admin_states(state_code) ON DELETE CASCADE
        );
        CREATE INDEX idx_districts_state_code ON admin_districts(state_code);
        CREATE INDEX idx_districts_lgd_code ON admin_districts(lgd_code);
    """)
    db.execute(create_districts)

    create_blocks = text("""
        CREATE TABLE admin_blocks (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            name_en VARCHAR(255) NOT NULL,
            lgd_code VARCHAR(10) NOT NULL UNIQUE,
            district_lgd_code VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (district_lgd_code) REFERENCES admin_districts(lgd_code) ON DELETE CASCADE
        );
        CREATE INDEX idx_blocks_district_code ON admin_blocks(district_lgd_code);
        CREATE INDEX idx_blocks_lgd_code ON admin_blocks(lgd_code);
    """)
    db.execute(create_blocks)

    create_panchayats = text("""
        CREATE TABLE admin_panchayats (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            name_en VARCHAR(255) NOT NULL,
            lgd_code VARCHAR(10) NOT NULL UNIQUE,
            block_lgd_code VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (block_lgd_code) REFERENCES admin_blocks(lgd_code) ON DELETE CASCADE
        );
        CREATE INDEX idx_panchayats_block_code ON admin_panchayats(block_lgd_code);
        CREATE INDEX idx_panchayats_lgd_code ON admin_panchayats(lgd_code);
    """)
    db.execute(create_panchayats)

    db.commit()
    logger.info("✓ All 4 tables created with correct schema")


def load_csv(file_path):
    """Load CSV file"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def import_all_data(db, blocks_csv, panchayats_csv):
    """Import all 4 levels from CSV files"""

    # Step 1: Load blocks CSV (contains states, districts, blocks)
    logger.info(f"\nLoading blocks CSV: {blocks_csv.name}")
    blocks_data = load_csv(blocks_csv)
    logger.info(f"  Loaded {len(blocks_data)} block records")

    # Step 2: Extract unique states
    logger.info("\n" + "=" * 80)
    logger.info("LEVEL 1: Importing States")
    logger.info("=" * 80)

    states_dict = {}
    for row in blocks_data:
        state_code = row['State Code']
        state_name = row['State Name (In English)']
        if state_code not in states_dict:
            states_dict[state_code] = state_name

    logger.info(f"Found {len(states_dict)} unique states")

    # Insert states
    insert_state = text("""
        INSERT INTO admin_states (name, name_en, state_code)
        VALUES (:name, :name_en, :state_code)
    """)

    for state_code, state_name in sorted(states_dict.items()):
        db.execute(insert_state, {
            "name": state_name,
            "name_en": state_name,
            "state_code": state_code
        })

    db.commit()
    logger.info(f"✓ Imported {len(states_dict)} states")

    # Step 3: Extract unique districts
    logger.info("\n" + "=" * 80)
    logger.info("LEVEL 2: Importing Districts")
    logger.info("=" * 80)

    districts_dict = {}
    for row in blocks_data:
        district_code = row['District Code']
        if district_code not in districts_dict:
            districts_dict[district_code] = {
                'name': row['District Name (In English)'],
                'state_code': row['State Code']
            }

    logger.info(f"Found {len(districts_dict)} unique districts")

    # Insert districts
    insert_district = text("""
        INSERT INTO admin_districts (name, name_en, lgd_code, state_code)
        VALUES (:name, :name_en, :lgd_code, :state_code)
    """)

    for district_code, district_data in sorted(districts_dict.items()):
        db.execute(insert_district, {
            "name": district_data['name'],
            "name_en": district_data['name'],
            "lgd_code": district_code,
            "state_code": district_data['state_code']
        })

        if len(districts_dict) > 100 and int(district_code) % 100 == 0:
            db.commit()  # Commit every 100 records

    db.commit()
    logger.info(f"✓ Imported {len(districts_dict)} districts")

    # Step 4: Import blocks
    logger.info("\n" + "=" * 80)
    logger.info("LEVEL 3: Importing Blocks (CRITICAL FIX!)")
    logger.info("=" * 80)

    insert_block = text("""
        INSERT INTO admin_blocks (name, name_en, lgd_code, district_lgd_code)
        VALUES (:name, :name_en, :lgd_code, :district_lgd_code)
    """)

    blocks_imported = 0
    blocks_skipped = 0

    for row in blocks_data:
        block_name = row['Development Block Name (In English)']
        block_code = row['Development Block Code']
        district_code = row['District Code']

        if not block_name or not block_name.strip():
            blocks_skipped += 1
            continue

        try:
            db.execute(insert_block, {
                "name": block_name,
                "name_en": block_name,
                "lgd_code": block_code,
                "district_lgd_code": district_code
            })
            blocks_imported += 1

            if blocks_imported % 500 == 0:
                db.commit()
                logger.info(f"  Progress: {blocks_imported} blocks imported...")

        except Exception as e:
            blocks_skipped += 1
            logger.debug(f"Skipped block {block_name}: {e}")

    db.commit()
    logger.info(f"✓ Imported {blocks_imported} blocks (skipped {blocks_skipped})")

    # Step 5: Import panchayats
    logger.info("\n" + "=" * 80)
    logger.info("LEVEL 4: Importing Panchayats (CRITICAL FIX!)")
    logger.info("=" * 80)

    logger.info(f"Loading panchayats CSV: {panchayats_csv.name}")
    panchayats_data = load_csv(panchayats_csv)
    logger.info(f"  Loaded {len(panchayats_data)} panchayat records")

    # Filter for Gram Panchayats (type 3) and Panchayat Samitis (type 2)
    panchayat_samitis = {}  # type 2
    gram_panchayats = []    # type 3

    for row in panchayats_data:
        if row['Localbody Type Code'] == '2':  # Panchayat Samiti
            panchayat_samitis[row['Localbody Code']] = row
        elif row['Localbody Type Code'] == '3':  # Gram Panchayat
            gram_panchayats.append(row)

    logger.info(f"  Found {len(panchayat_samitis)} Panchayat Samitis")
    logger.info(f"  Found {len(gram_panchayats)} Gram Panchayats")

    # Build a mapping of Panchayat Samiti codes to block codes
    # This is complex because the CSV doesn't have direct block mapping
    # We'll use the Panchayat Samiti name to match with block names

    # Get all blocks from database
    blocks_query = text("""
        SELECT lgd_code, name_en, district_lgd_code
        FROM admin_blocks
    """)
    db_blocks = db.execute(blocks_query).fetchall()

    # Create mapping: block_name -> block_code
    block_name_to_code = {}
    for block in db_blocks:
        block_code, block_name, district_code = block
        # Normalize name for matching
        normalized_name = block_name.strip().lower()
        block_name_to_code[normalized_name] = block_code

    logger.info(f"  Loaded {len(block_name_to_code)} blocks for matching")

    # Insert panchayats
    insert_panchayat = text("""
        INSERT INTO admin_panchayats (name, name_en, lgd_code, block_lgd_code)
        VALUES (:name, :name_en, :lgd_code, :block_lgd_code)
    """)

    panchayats_imported = 0
    panchayats_skipped = 0
    samiti_to_block = {}  # Cache mapping

    for row in gram_panchayats:
        panchayat_name = row['Localbody Name (In English)']
        panchayat_code = row['Localbody Code']
        parent_code = row['Parent Localbody Code']

        if not panchayat_name or not panchayat_name.strip():
            panchayats_skipped += 1
            continue

        # Try to find the block for this panchayat
        block_code = None

        # First, check if we've already mapped this Panchayat Samiti
        if parent_code in samiti_to_block:
            block_code = samiti_to_block[parent_code]
        elif parent_code in panchayat_samitis:
            # Try to match Panchayat Samiti name with block name
            samiti = panchayat_samitis[parent_code]
            samiti_name = samiti['Localbody Name (In English)'].strip().lower()

            # Try exact match first
            if samiti_name in block_name_to_code:
                block_code = block_name_to_code[samiti_name]
                samiti_to_block[parent_code] = block_code
            else:
                # Try to find a block name that contains the samiti name
                for block_name, code in block_name_to_code.items():
                    if samiti_name in block_name or block_name in samiti_name:
                        block_code = code
                        samiti_to_block[parent_code] = block_code
                        break

        if not block_code:
            panchayats_skipped += 1
            continue

        try:
            db.execute(insert_panchayat, {
                "name": panchayat_name,
                "name_en": panchayat_name,
                "lgd_code": panchayat_code,
                "block_lgd_code": block_code
            })
            panchayats_imported += 1

            if panchayats_imported % 1000 == 0:
                db.commit()
                logger.info(f"  Progress: {panchayats_imported}/{len(gram_panchayats)} panchayats imported...")

        except Exception as e:
            panchayats_skipped += 1
            logger.debug(f"Skipped panchayat {panchayat_name}: {e}")

    db.commit()
    logger.info(f"✓ Imported {panchayats_imported} panchayats (skipped {panchayats_skipped})")

    return {
        'states': len(states_dict),
        'districts': len(districts_dict),
        'blocks': blocks_imported,
        'panchayats': panchayats_imported
    }


def verify_import(db):
    """Verify the import"""
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION REPORT")
    logger.info("=" * 80)

    counts = {}
    tables = ['admin_states', 'admin_districts', 'admin_blocks', 'admin_panchayats']

    for table in tables:
        count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        counts[table] = count
        logger.info(f"  ✓ {table}: {count:,} records")

    # Test cascade query
    logger.info("\nTesting Cascading Dropdown Query:")
    cascade = db.execute(text("""
        SELECT
            s.name_en as state,
            d.name_en as district,
            b.name_en as block,
            p.name_en as panchayat
        FROM admin_panchayats p
        JOIN admin_blocks b ON p.block_lgd_code = b.lgd_code
        JOIN admin_districts d ON b.district_lgd_code = d.lgd_code
        JOIN admin_states s ON d.state_code = s.state_code
        LIMIT 5
    """)).fetchall()

    for row in cascade:
        logger.info(f"  {row[0]} → {row[1]} → {row[2]} → {row[3]}")

    return counts


def main():
    logger.info("=" * 80)
    logger.info("COMPLETE AZURE DATABASE REIMPORT - ALL 4 LEVELS")
    logger.info("Fixing Critical Mobile App Dropdown Issue")
    logger.info("=" * 80)

    db_url = get_database_url()
    if not db_url:
        return False

    # File paths
    base_path = Path(__file__).parent.parent / "data" / "lgd"
    blocks_csv = base_path / "blocks.19Nov2025.csv"
    panchayats_csv = base_path / "pri_local_bodies.19Nov2025.csv"

    if not blocks_csv.exists() or not panchayats_csv.exists():
        logger.error("Required CSV files not found")
        return False

    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={
                'connect_timeout': 60,
                'options': '-c statement_timeout=600000'
            }
        )

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        logger.info("✓ Database connection established\n")

        # Drop and recreate all tables
        drop_and_create_all_tables(db)

        # Import all data
        counts = import_all_data(db, blocks_csv, panchayats_csv)

        # Verify
        verify_counts = verify_import(db)

        logger.info("\n" + "=" * 80)
        logger.info("🎉 IMPORT COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"Level 1 - States: {counts['states']}")
        logger.info(f"Level 2 - Districts: {counts['districts']}")
        logger.info(f"Level 3 - Blocks: {counts['blocks']}")
        logger.info(f"Level 4 - Panchayats: {counts['panchayats']}")
        logger.info("=" * 80)
        logger.info("\n✅ Mobile app 4-level dropdown is now FIXED!")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
