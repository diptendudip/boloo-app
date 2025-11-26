#!/usr/bin/env python3
"""
Import Gram Panchayats from LGD CSV data into PostgreSQL

This script imports panchayat data from the official LGD (Local Government Directory)
CSV dumps into the admin_panchayats table.

Usage:
    python3 scripts/import_lgd_panchayats.py [--state STATE_CODE]

Examples:
    python3 scripts/import_lgd_panchayats.py              # Import all states
    python3 scripts/import_lgd_panchayats.py --state 22   # Import only Chhattisgarh
"""

import csv
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import execute_batch
import argparse

# Database connection
DB_CONFIG = {
    'dbname': 'boloo',
    'user': 'boloo',
    'password': 'boloo_dev_password',
    'host': 'localhost',
    'port': '5432'
}

DATA_DIR = Path(__file__).parent.parent / 'data' / 'lgd'
PRI_FILE = DATA_DIR / 'pri_local_bodies.19Nov2025.csv'
BLOCKS_FILE = DATA_DIR / 'blocks.19Nov2025.csv'


def load_blocks_mapping():
    """Load block code to LGD code mapping"""
    print("📖 Loading blocks mapping...")
    blocks_map = {}

    with open(BLOCKS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            block_code = row['Development Block Code']
            blocks_map[block_code] = {
                'lgd_code': block_code,
                'district_code': row['District Code'],
                'state_code': row['State Code']
            }

    print(f"✅ Loaded {len(blocks_map)} blocks")
    return blocks_map


def import_panchayats(state_code=None, batch_size=1000, force=False):
    """Import panchayats from CSV to database"""

    # Load blocks mapping first
    blocks_map = load_blocks_mapping()

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Read CSV and prepare data
        print(f"📂 Reading panchayats from {PRI_FILE}")
        panchayats = []
        skipped = 0
        total_read = 0

        with open(PRI_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                total_read += 1

                # Filter by state if specified
                if state_code and row['State Code'] != state_code:
                    continue

                # Only process Gram Panchayats
                if row['Localbody Type Name'] != 'Gram Panchayat':
                    continue

                parent_code = row['Parent Localbody Code']

                # Check if parent block exists in our mapping
                if parent_code not in blocks_map:
                    skipped += 1
                    if skipped <= 5:  # Show first 5 warnings
                        print(f"⚠️  Skipping {row['Localbody Name (In English)']} - parent block {parent_code} not found")
                    continue

                panchayat = {
                    'name': row['Localbody Name (In Local)'] or row['Localbody Name (In English)'],
                    'name_en': row['Localbody Name (In English)'],
                    'lgd_code': row['Localbody Code'],
                    'block_lgd_code': parent_code
                }

                panchayats.append(panchayat)

        print(f"\n📊 Statistics:")
        print(f"   Total rows read: {total_read}")
        print(f"   Panchayats to import: {len(panchayats)}")
        print(f"   Skipped (no parent block): {skipped}")

        if not panchayats:
            print("❌ No panchayats to import!")
            return

        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM admin_panchayats")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"\n⚠️  WARNING: {existing_count} panchayats already exist in database")

            if not force:
                response = input("   Delete existing data and reimport? [yes/no]: ")
                if response.lower() != 'yes':
                    print("❌ Import cancelled")
                    return
            else:
                print("   --force flag set, automatically deleting...")

            print("🗑️  Deleting existing panchayats...")
            cursor.execute("DELETE FROM admin_panchayats")
            conn.commit()
            print(f"   Deleted {cursor.rowcount} records")

        # Insert panchayats in batches
        print(f"\n💾 Importing {len(panchayats)} panchayats...")

        insert_query = """
            INSERT INTO admin_panchayats (name, name_en, lgd_code, block_lgd_code)
            VALUES (%(name)s, %(name_en)s, %(lgd_code)s, %(block_lgd_code)s)
            ON CONFLICT (lgd_code) DO UPDATE SET
                name = EXCLUDED.name,
                name_en = EXCLUDED.name_en,
                block_lgd_code = EXCLUDED.block_lgd_code
        """

        # Import in batches
        for i in range(0, len(panchayats), batch_size):
            batch = panchayats[i:i + batch_size]
            execute_batch(cursor, insert_query, batch)
            conn.commit()

            progress = min(i + batch_size, len(panchayats))
            percent = (progress / len(panchayats)) * 100
            print(f"   Progress: {progress}/{len(panchayats)} ({percent:.1f}%)")

        # Verify import
        cursor.execute("SELECT COUNT(*) FROM admin_panchayats")
        final_count = cursor.fetchone()[0]

        print(f"\n✅ Import complete!")
        print(f"   Total panchayats in database: {final_count}")

        # Show sample data
        if state_code:
            print(f"\n📍 Sample data for state {state_code}:")
            cursor.execute("""
                SELECT p.name_en, p.lgd_code, p.block_lgd_code, b.name_en as block_name
                FROM admin_panchayats p
                LEFT JOIN admin_blocks b ON b.lgd_code = p.block_lgd_code
                LEFT JOIN admin_districts d ON d.lgd_code = b.district_lgd_code
                WHERE d.state_code = %s
                LIMIT 5
            """, (state_code,))

            for row in cursor.fetchall():
                print(f"   - {row[0]} (Block: {row[3]})")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Import LGD Panchayat data to PostgreSQL')
    parser.add_argument('--state', type=str, help='State code to import (e.g., 22 for Chhattisgarh)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for inserts')
    parser.add_argument('--force', action='store_true', help='Force delete existing data without prompt')

    args = parser.parse_args()

    print("=" * 60)
    print("   LGD Panchayat Data Import")
    print("=" * 60)
    print()

    # Check if data files exist
    if not PRI_FILE.exists():
        print(f"❌ Error: PRI file not found at {PRI_FILE}")
        print("   Run this command first to download data:")
        print("   cd backend/data/lgd && curl -L -o pri_local_bodies.csv.7z ...")
        sys.exit(1)

    if not BLOCKS_FILE.exists():
        print(f"❌ Error: Blocks file not found at {BLOCKS_FILE}")
        sys.exit(1)

    # Run import
    state_name = f"state {args.state}" if args.state else "all states"
    print(f"🚀 Starting import for {state_name}...\n")

    import_panchayats(state_code=args.state, batch_size=args.batch_size, force=args.force)

    print("\n" + "=" * 60)
    print("✨ Import process completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
