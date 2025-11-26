#!/usr/bin/env python3
"""
Fresh LGD Import - Hybrid Approach (Multi-State)

This script implements the EXPERT HYBRID APPROACH:
1. Import Development Blocks from blocks.csv for multiple states
2. Map Janpad Panchayats to Development Blocks (co-terminus, same geography)
3. Link Gram Panchayats through their Janpad parent to Development Blocks

Key Insight: Development Block = geographical area
             Janpad Panchayat = governance body in that area
             They are CO-TERMINUS (same boundaries)

Target States: Chhattisgarh, Madhya Pradesh, Maharashtra, Jharkhand,
               Bihar, Uttar Pradesh, Andhra Pradesh, Telangana, Odisha
"""

import csv
import sys
from pathlib import Path
from difflib import SequenceMatcher
import argparse

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
BLOCKS_FILE = DATA_DIR / 'blocks.19Nov2025.csv'
PRI_FILE = DATA_DIR / 'pri_local_bodies.19Nov2025.csv'

# State codes for target states
TARGET_STATES = {
    '22': 'Chhattisgarh',
    '23': 'Madhya Pradesh',
    '27': 'Maharashtra',
    '20': 'Jharkhand',
    '10': 'Bihar',
    '09': 'Uttar Pradesh',
    '28': 'Andhra Pradesh',
    '36': 'Telangana',
    '21': 'Odisha'
}


def similarity_score(a, b):
    """Calculate similarity between two strings (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def main(state_codes=None):
    if state_codes is None:
        state_codes = list(TARGET_STATES.keys())

    state_names = [TARGET_STATES[code] for code in state_codes]

    print("=" * 80)
    print("   FRESH LGD IMPORT - HYBRID APPROACH (MULTI-STATE)")
    print("=" * 80)
    print()
    print("Target States:", ", ".join(state_names))
    print()
    print("Strategy: Development Blocks are CO-TERMINUS with Janpad Panchayats")
    print("          We'll map them by geography and name similarity")
    print()

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # =====================================================================
        # STEP 1: Import Development Blocks for target states
        # =====================================================================
        print("📖 STEP 1: Loading Development Blocks from blocks.csv...")

        blocks = []
        with open(BLOCKS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['State Code'] not in state_codes:
                    continue

                blocks.append({
                    'lgd_code': row['Development Block Code'],
                    'name': row['Development Block Name (In Local)'] or row['Development Block Name (In English)'],
                    'name_en': row['Development Block Name (In English)'],
                    'district_code': row['District Code']
                })

        print(f"✅ Found {len(blocks)} Development Blocks for target states")

        # Get district name to LGD code mapping from database for target states
        placeholders = ','.join(['%s'] * len(state_codes))
        cursor.execute(f"SELECT name_en, lgd_code, state_code FROM admin_districts WHERE state_code IN ({placeholders})", state_codes)
        district_name_to_lgd = {}
        for row in cursor.fetchall():
            # Use (state_code, district_name) as key for uniqueness across states
            district_name_to_lgd[(row[2], row[0])] = row[1]

        print(f"✅ Found {len(district_name_to_lgd)} districts in database")

        # Re-read blocks with district names and map to database
        blocks_with_db_district = []
        with open(BLOCKS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['State Code'] not in state_codes:
                    continue

                district_name = row['District Name (In English)']
                state_code = row['State Code']

                # Match district name to database using (state_code, district_name)
                key = (state_code, district_name)
                if key in district_name_to_lgd:
                    blocks_with_db_district.append({
                        'lgd_code': row['Development Block Code'],
                        'name': row['Development Block Name (In Local)'] or row['Development Block Name (In English)'],
                        'name_en': row['Development Block Name (In English)'],
                        'district_lgd_code': district_name_to_lgd[key]
                    })

        print(f"✅ Mapped {len(blocks_with_db_district)} blocks to database districts")

        # Clear old blocks for target states
        print("\n🗑️  Clearing old blocks for target states...")
        cursor.execute(f"""
            DELETE FROM admin_blocks
            WHERE district_lgd_code IN (
                SELECT lgd_code FROM admin_districts WHERE state_code IN ({placeholders})
            )
        """, state_codes)
        print(f"   Deleted {cursor.rowcount} old blocks")

        # Insert Development Blocks
        print("\n💾 Importing Development Blocks...")
        insert_query = """
            INSERT INTO admin_blocks (name, name_en, lgd_code, district_lgd_code)
            VALUES (%(name)s, %(name_en)s, %(lgd_code)s, %(district_lgd_code)s)
            ON CONFLICT (lgd_code) DO UPDATE SET
                name = EXCLUDED.name,
                name_en = EXCLUDED.name_en,
                district_lgd_code = EXCLUDED.district_lgd_code
        """
        execute_batch(cursor, insert_query, blocks_with_db_district)
        conn.commit()
        print(f"✅ Imported {len(blocks_with_db_district)} Development Blocks")

        # =====================================================================
        # STEP 2: Load Janpad/Block Panchayats for target states
        # =====================================================================
        print("\n📖 STEP 2: Loading Janpad/Block Panchayats...")

        janpads = {}
        with open(PRI_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['State Code'] not in state_codes:
                    continue

                if row['Localbody Type Name'] in ['Janpad Panchayat', 'Block Panchayat', 'Panchayat Samiti']:
                    janpad_code = row['Localbody Code']
                    janpads[janpad_code] = {
                        'name_en': row['Localbody Name (In English)'],
                        'parent_zila': row['Parent Localbody Code'],  # Zila Panchayat
                        'state_code': row['State Code']
                    }

        print(f"✅ Found {len(janpads)} Janpad/Block Panchayats")

        # Load Zila Panchayats to get district mapping
        print("\n📖 STEP 3: Loading Zila/District Panchayats...")

        zilas = {}
        with open(PRI_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['State Code'] not in state_codes:
                    continue

                if row['Localbody Type Name'] in ['Zila Panchayat', 'District Panchayat']:
                    zila_code = row['Localbody Code']
                    zilas[zila_code] = {
                        'name_en': row['Localbody Name (In English)'],
                        'state_code': row['State Code']
                    }

        print(f"✅ Found {len(zilas)} Zila/District Panchayats")

        # Get district name to lgd_code mapping for target states
        cursor.execute(f"SELECT name_en, lgd_code, state_code FROM admin_districts WHERE state_code IN ({placeholders})", state_codes)
        district_lookup = {}
        for row in cursor.fetchall():
            # Use (state_code, district_name) as key
            district_lookup[(row[2], row[0])] = row[1]

        # Map Janpads to Development Blocks
        print("\n🔗 STEP 4: Mapping Janpads to Development Blocks...")

        janpad_to_block = {}
        mapping_stats = {'exact': 0, 'fuzzy': 0, 'failed': 0}

        for janpad_code, janpad_data in janpads.items():
            janpad_name = janpad_data['name_en']
            zila_code = janpad_data['parent_zila']
            state_code = janpad_data['state_code']

            # Get district from Zila
            if zila_code not in zilas:
                mapping_stats['failed'] += 1
                continue

            zila_name = zilas[zila_code]['name_en']

            # Match Zila name to District using state_code
            district_lgd = None
            key = (state_code, zila_name)
            if key in district_lookup:
                district_lgd = district_lookup[key]
            else:
                # Fuzzy match within same state
                for (s_code, dist_name), dist_lgd in district_lookup.items():
                    if s_code == state_code and similarity_score(zila_name, dist_name) > 0.8:
                        district_lgd = dist_lgd
                        break

            if not district_lgd:
                mapping_stats['failed'] += 1
                continue

            # Find Development Block with same name in this district
            matched_block = None
            best_score = 0

            for block in blocks_with_db_district:
                if block['district_lgd_code'] != district_lgd:
                    continue

                score = similarity_score(janpad_name, block['name_en'])
                if score > best_score:
                    best_score = score
                    matched_block = block['lgd_code']

            if matched_block and best_score > 0.6:  # 60% similarity threshold
                janpad_to_block[janpad_code] = matched_block
                if best_score > 0.95:
                    mapping_stats['exact'] += 1
                else:
                    mapping_stats['fuzzy'] += 1
            else:
                mapping_stats['failed'] += 1

        print(f"✅ Mapping complete:")
        print(f"   - Exact matches: {mapping_stats['exact']}")
        print(f"   - Fuzzy matches: {mapping_stats['fuzzy']}")
        print(f"   - Failed: {mapping_stats['failed']}")
        print(f"   - Total mapped: {len(janpad_to_block)}/{len(janpads)}")

        # =====================================================================
        # STEP 5: Import Gram Panchayats for target states
        # =====================================================================
        print("\n📖 STEP 5: Loading Gram Panchayats...")

        gram_panchayats = []
        skipped = 0

        with open(PRI_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['State Code'] not in state_codes:
                    continue

                if row['Localbody Type Name'] == 'Gram Panchayat':
                    parent_janpad = row['Parent Localbody Code']

                    # Map Janpad to Development Block
                    if parent_janpad in janpad_to_block:
                        block_code = janpad_to_block[parent_janpad]
                        gram_panchayats.append({
                            'name': row['Localbody Name (In Local)'] or row['Localbody Name (In English)'],
                            'name_en': row['Localbody Name (In English)'],
                            'lgd_code': row['Localbody Code'],
                            'block_lgd_code': block_code
                        })
                    else:
                        skipped += 1

        print(f"✅ Found {len(gram_panchayats)} Gram Panchayats to import")
        print(f"⚠️  Skipped {skipped} GPs (Janpad not mapped)")

        # Clear old panchayats for target states
        print("\n🗑️  Clearing old panchayats for target states...")
        cursor.execute(f"""
            DELETE FROM admin_panchayats
            WHERE block_lgd_code IN (
                SELECT lgd_code FROM admin_blocks
                WHERE district_lgd_code IN (
                    SELECT lgd_code FROM admin_districts WHERE state_code IN ({placeholders})
                )
            )
        """, state_codes)
        print(f"   Deleted {cursor.rowcount} old panchayats")

        # Insert Gram Panchayats
        print("\n💾 Importing Gram Panchayats...")
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

        # =====================================================================
        # STEP 6: Verification
        # =====================================================================
        print("\n📊 STEP 6: Verification...")

        cursor.execute("""
            SELECT COUNT(*)
            FROM admin_blocks
            WHERE district_lgd_code IN (
                SELECT lgd_code FROM admin_districts WHERE state_code = '22'
            )
        """)
        block_count = cursor.fetchone()[0]
        print(f"✅ Total blocks in database: {block_count}")

        cursor.execute("SELECT COUNT(*) FROM admin_panchayats")
        panchayat_count = cursor.fetchone()[0]
        print(f"✅ Total panchayats in database: {panchayat_count}")

        # Show sample by state
        print("\n📍 Sample data by state:")
        for state_code in state_codes[:3]:  # Show first 3 states
            state_name = TARGET_STATES[state_code]
            cursor.execute("""
                SELECT COUNT(DISTINCT b.lgd_code)
                FROM admin_blocks b
                JOIN admin_districts d ON d.lgd_code = b.district_lgd_code
                WHERE d.state_code = %s
            """, (state_code,))
            block_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM admin_panchayats p
                JOIN admin_blocks b ON b.lgd_code = p.block_lgd_code
                JOIN admin_districts d ON d.lgd_code = b.district_lgd_code
                WHERE d.state_code = %s
            """, (state_code,))
            gp_count = cursor.fetchone()[0]

            print(f"   {state_name}: {block_count} blocks, {gp_count} panchayats")

        # Show sample hierarchy
        print("\n📍 Sample hierarchy:")
        cursor.execute(f"""
            SELECT
                d.name_en as district,
                b.name_en as block,
                p.name_en as panchayat
            FROM admin_panchayats p
            JOIN admin_blocks b ON b.lgd_code = p.block_lgd_code
            JOIN admin_districts d ON d.lgd_code = b.district_lgd_code
            WHERE d.state_code IN ({placeholders})
            ORDER BY d.name_en, b.name_en, p.name_en
            LIMIT 10
        """, state_codes)

        for row in cursor.fetchall():
            print(f"   {row[0]} → {row[1]} → {row[2]}")

        print("\n" + "=" * 80)
        print("✅ IMPORT COMPLETE!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import LGD data for multiple states')
    parser.add_argument('--states', nargs='+', help='State codes to import (default: all target states)')
    parser.add_argument('--all', action='store_true', help='Import all states')

    args = parser.parse_args()

    if args.all:
        print("⚠️  Importing ALL states - this will take 10-15 minutes...")
        main(state_codes=None)  # Will use all TARGET_STATES
    elif args.states:
        main(state_codes=args.states)
    else:
        main()  # Use all TARGET_STATES by default
