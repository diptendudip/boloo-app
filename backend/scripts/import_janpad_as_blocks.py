#!/usr/bin/env python3
"""
Import Janpad Panchayats as blocks and link Gram Panchayats to them

This script:
1. Imports Janpad/Block Panchayats as blocks
2. Imports Gram Panchayats linked to Janpads
3. Works with current LGD data structure
"""

import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import execute_batch

DB_CONFIG = {
    'dbname': 'boloo',
    'user': 'boloo',
    'password': 'boloo_dev_password',
    'host': 'localhost',
    'port': '5432'
}

DATA_DIR = Path(__file__).parent.parent / 'data' / 'lgd'
PRI_FILE = DATA_DIR / 'pri_local_bodies.19Nov2025.csv'

def main():
    print("=" * 70)
    print("   Import Janpad Panchayats as Blocks + Gram Panchayats")
    print("=" * 70)
    print()

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Step 1: Load Janpad/Block Panchayats for Chhattisgarh
        print("📖 Step 1: Loading Janpad/Block Panchayats...")
        janpads = {}
        janpad_blocks = []

        with open(PRI_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['State Name'] != 'Chhattisgarh':
                    continue

                if row['Localbody Type Name'] in ['Janpad Panchayat', 'Block Panchayat']:
                    janpad_code = row['Localbody Code']
                    janpads[janpad_code] = {
                        'name': row['Localbody Name (In Local)'] or row['Localbody Name (In English)'],
                        'name_en': row['Localbody Name (In English)'],
                        'parent': row['Parent Localbody Code']  # This is district
                    }

        print(f"✅ Found {len(janpads)} Janpad/Block Panchayats")

        # Step 2: Load blocks CSV to get district mapping
        print("\n📖 Step 2: Loading blocks CSV for district mapping...")

        blocks_file = DATA_DIR / 'blocks.19Nov2025.csv'
        block_to_district = {}

        with open(blocks_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['State Code'] == '22':  # Chhattisgarh
                    block_code = row['Development Block Code']
                    district_name = row['District Name (In English)']
                    block_to_district[block_code] = district_name

        print(f"✅ Found {len(block_to_district)} blocks from CSV")

        # Get district name to lgd_code mapping from database
        cursor.execute("SELECT name_en, lgd_code FROM admin_districts WHERE state_code = '22'")
        district_name_to_lgd = {row[0]: row[1] for row in cursor.fetchall()}

        print(f"✅ Found {len(district_name_to_lgd)} districts in database")

        # Map Janpads to blocks to districts
        # Strategy: Use block names to match Janpads with districts
        for janpad_code, janpad_data in janpads.items():
            janpad_name = janpad_data['name_en']

            # Try to find matching district by janpad name
            # (Many Janpads are named after their district)
            district_lgd = None

            # Try exact match first
            if janpad_name in district_name_to_lgd:
                district_lgd = district_name_to_lgd[janpad_name]
            else:
                # Try partial match
                for dist_name, dist_lgd in district_name_to_lgd.items():
                    if janpad_name.lower() in dist_name.lower() or dist_name.lower() in janpad_name.lower():
                        district_lgd = dist_lgd
                        break

            if district_lgd:
                janpad_blocks.append({
                    'lgd_code': janpad_code,
                    'name': janpad_data['name'],
                    'name_en': janpad_data['name_en'],
                    'district_lgd_code': district_lgd
                })

        print(f"✅ Mapped {len(janpad_blocks)} Janpads to districts")

        # Step 3: Clear and import blocks
        print("\n📖 Step 3: Importing Janpads as blocks...")

        # Delete Chhattisgarh blocks
        cursor.execute("""
            DELETE FROM admin_blocks
            WHERE district_lgd_code IN (
                SELECT lgd_code FROM admin_districts WHERE state_code = '22'
            )
        """)
        print(f"   Deleted {cursor.rowcount} old Chhattisgarh blocks")

        # Insert Janpads as blocks
        insert_query = """
            INSERT INTO admin_blocks (name, name_en, lgd_code, district_lgd_code)
            VALUES (%(name)s, %(name_en)s, %(lgd_code)s, %(district_lgd_code)s)
            ON CONFLICT (lgd_code) DO UPDATE SET
                name = EXCLUDED.name,
                name_en = EXCLUDED.name_en,
                district_lgd_code = EXCLUDED.district_lgd_code
        """
        execute_batch(cursor, insert_query, janpad_blocks)
        conn.commit()
        print(f"✅ Imported {len(janpad_blocks)} Janpad/Block Panchayats as blocks")

        # Step 4: Import Gram Panchayats
        print("\n📖 Step 4: Importing Gram Panchayats...")

        gram_panchayats = []
        with open(PRI_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['State Name'] != 'Chhattisgarh':
                    continue

                if row['Localbody Type Name'] == 'Gram Panchayat':
                    parent_janpad = row['Parent Localbody Code']
                    if parent_janpad in janpads:
                        gram_panchayats.append({
                            'name': row['Localbody Name (In Local)'] or row['Localbody Name (In English)'],
                            'name_en': row['Localbody Name (In English)'],
                            'lgd_code': row['Localbody Code'],
                            'block_lgd_code': parent_janpad  # Link to Janpad
                        })

        print(f"✅ Found {len(gram_panchayats)} Gram Panchayats")

        # Delete old panchayats
        cursor.execute("DELETE FROM admin_panchayats")
        print(f"   Deleted {cursor.rowcount} old panchayats")

        # Insert Gram Panchayats
        insert_query = """
            INSERT INTO admin_panchayats (name, name_en, lgd_code, block_lgd_code)
            VALUES (%(name)s, %(name_en)s, %(lgd_code)s, %(block_lgd_code)s)
            ON CONFLICT (lgd_code) DO UPDATE SET
                name = EXCLUDED.name,
                name_en = EXCLUDED.name_en,
                block_lgd_code = EXCLUDED.block_lgd_code
        """

        batch_size = 1000
        for i in range(0, len(gram_panchayats), batch_size):
            batch = gram_panchayats[i:i + batch_size]
            execute_batch(cursor, insert_query, batch)
            conn.commit()
            progress = min(i + batch_size, len(gram_panchayats))
            print(f"   Progress: {progress}/{len(gram_panchayats)}")

        print(f"✅ Imported {len(gram_panchayats)} Gram Panchayats")

        # Step 5: Verify
        print("\n📖 Step 5: Verification...")
        cursor.execute("SELECT COUNT(*) FROM admin_blocks WHERE district_lgd_code IN (SELECT lgd_code FROM admin_districts WHERE state_code = '22')")
        block_count = cursor.fetchone()[0]
        print(f"✅ Blocks: {block_count}")

        cursor.execute("SELECT COUNT(*) FROM admin_panchayats")
        panchayat_count = cursor.fetchone()[0]
        print(f"✅ Panchayats: {panchayat_count}")

        # Show sample
        print("\n📍 Sample data:")
        cursor.execute("""
            SELECT p.name_en, b.name_en as block_name, d.name_en as district
            FROM admin_panchayats p
            JOIN admin_blocks b ON b.lgd_code = p.block_lgd_code
            JOIN admin_districts d ON d.lgd_code = b.district_lgd_code
            WHERE d.state_code = '22'
            LIMIT 5
        """)

        for row in cursor.fetchall():
            print(f"   - {row[0]} → {row[1]} → {row[2]}")

        print("\n✅ Import successful!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
