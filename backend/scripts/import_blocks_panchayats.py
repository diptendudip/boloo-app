#!/usr/bin/env python3
"""
Import Blocks and Panchayats data to Azure PostgreSQL
"""
import csv
import psycopg2
from psycopg2.extras import execute_batch
import sys

# Azure PostgreSQL connection
DB_CONFIG = {
    'host': 'boloo-database.postgres.database.azure.com',
    'database': 'flexibleserverdb',
    'user': 'booloadmin',
    'password': 'Boloo2025SecureDB!',
    'port': '5432',
    'sslmode': 'require'
}

def import_blocks():
    """Import blocks from blocks.19Nov2025.csv"""
    print("\n=== IMPORTING BLOCKS ===")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Create admin_blocks table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_blocks (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            name_en VARCHAR(255),
            lgd_code VARCHAR(50) UNIQUE NOT NULL,
            district_lgd_code VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Clear existing data
    cur.execute("DELETE FROM admin_blocks")
    print("✅ Cleared existing blocks")

    # Read CSV and prepare data
    blocks_data = []
    csv_path = '/Users/diptendu/boloo app/boloo-app/backend/data/lgd/blocks.19Nov2025.csv'

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Column mapping:
            # District Code (column 4) -> district_lgd_code
            # Development Block Code (column 6) -> lgd_code
            # Development Block Name (In English) (column 8) -> name_en
            district_code = row['District Code'].strip()
            block_code = row['Development Block Code'].strip()
            block_name_en = row['Development Block Name (In English)'].strip()
            block_name_local = row.get('Development Block Name (In Local)', '').strip() or block_name_en

            if block_code and district_code:
                blocks_data.append((
                    block_name_local,
                    block_name_en,
                    block_code,
                    district_code
                ))

    print(f"📊 Prepared {len(blocks_data)} blocks for import")

    # Batch insert
    insert_query = """
        INSERT INTO admin_blocks (name, name_en, lgd_code, district_lgd_code)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (lgd_code) DO NOTHING
    """

    execute_batch(cur, insert_query, blocks_data, page_size=1000)
    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM admin_blocks")
    count = cur.fetchone()[0]
    print(f"✅ Imported {count} blocks successfully")

    # Sample data
    cur.execute("SELECT lgd_code, name_en, district_lgd_code FROM admin_blocks LIMIT 5")
    print("\n📋 Sample blocks:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} (District: {row[2]})")

    cur.close()
    conn.close()
    return count

def import_panchayats():
    """Import panchayats from pri_local_bodies.19Nov2025.csv"""
    print("\n=== IMPORTING PANCHAYATS ===")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Create admin_panchayats table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_panchayats (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            name_en VARCHAR(255),
            lgd_code VARCHAR(50) UNIQUE NOT NULL,
            block_lgd_code VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Clear existing data
    cur.execute("DELETE FROM admin_panchayats")
    print("✅ Cleared existing panchayats")

    # First, let's understand the data structure
    csv_path = '/Users/diptendu/boloo app/boloo-app/backend/data/lgd/pri_local_bodies.19Nov2025.csv'

    # Analyze localbody types
    type_counts = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            type_code = row['Localbody Type Code'].strip()
            type_name = row['Localbody Type Name'].strip()
            type_counts[f"{type_code}:{type_name}"] = type_counts.get(f"{type_code}:{type_name}", 0) + 1

    print("\n📊 Localbody type distribution:")
    for type_info, count in sorted(type_counts.items()):
        print(f"  {type_info}: {count:,} records")

    # Now import - we'll import all types but mark the type
    # Type 3 (Gram Panchayat) and Type 4 (Nagar Panchayat) are the village-level panchayats
    panchayats_data = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            localbody_code = row['Localbody Code'].strip()
            localbody_name_en = row['Localbody Name (In English)'].strip()
            localbody_name_local = row['Localbody Name (In Local)'].strip() or localbody_name_en
            parent_code = row['Parent Localbody Code'].strip()
            type_code = int(row['Localbody Type Code'].strip())

            # Only import Type 3 (Gram Panchayat/Village Panchayat) - village level
            # Type 1 = District level, Type 2 = Block level, Type 3 = Village level
            if localbody_code and type_code == 3:
                panchayats_data.append((
                    localbody_name_local,
                    localbody_name_en,
                    localbody_code,
                    parent_code if parent_code != '0' else None
                ))

            # Progress indicator
            if (i + 1) % 50000 == 0:
                print(f"  Processed {i + 1:,} records...")

    print(f"\n📊 Prepared {len(panchayats_data):,} panchayat records for import")

    # Batch insert
    insert_query = """
        INSERT INTO admin_panchayats (name, name_en, lgd_code, block_lgd_code)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (lgd_code) DO NOTHING
    """

    print("⏳ Importing in batches...")
    for i in range(0, len(panchayats_data), 5000):
        batch = panchayats_data[i:i+5000]
        execute_batch(cur, insert_query, batch, page_size=1000)
        conn.commit()
        print(f"  Imported {min(i + 5000, len(panchayats_data)):,}/{len(panchayats_data):,}")

    # Verify
    cur.execute("SELECT COUNT(*) FROM admin_panchayats")
    count = cur.fetchone()[0]
    print(f"\n✅ Imported {count:,} panchayats successfully")

    # Sample data
    cur.execute("""
        SELECT lgd_code, name_en, block_lgd_code
        FROM admin_panchayats
        LIMIT 5
    """)
    print("\n📋 Sample panchayats:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} (Parent: {row[2]})")

    cur.close()
    conn.close()
    return count

def main():
    try:
        print("🚀 Starting LGD Data Import to Azure PostgreSQL")
        print(f"📍 Database: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

        # Import blocks
        blocks_count = import_blocks()

        # Import panchayats
        panchayats_count = import_panchayats()

        print("\n" + "="*60)
        print("✅ IMPORT COMPLETE!")
        print("="*60)
        print(f"Blocks: {blocks_count:,}")
        print(f"Panchayats: {panchayats_count:,}")
        print("\n🎯 Next: Test the dropdown APIs")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
