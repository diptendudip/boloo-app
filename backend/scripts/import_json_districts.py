#!/usr/bin/env python3
"""
Import Districts from JSON - Complete All-India Data
Downloads and imports all districts for all Indian states from GitHub JSON source
"""

import json
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_database_url():
    """Get database URL from environment or use default"""
    return os.getenv("DATABASE_URL", "postgresql://boloo:boloo_dev_password@localhost:5432/boloo")


def import_districts_from_json():
    """Import complete district data from JSON file"""

    print("\n" + "="*70)
    print("🇮🇳 IMPORTING ALL-INDIA DISTRICTS FROM JSON")
    print("="*70 + "\n")

    # Path to JSON file
    json_file = Path(__file__).parent.parent / "data" / "lgd" / "states-districts.json"

    if not json_file.exists():
        print(f"❌ JSON file not found at: {json_file}")
        print("Please run: curl -L -o backend/data/lgd/states-districts.json 'https://raw.githubusercontent.com/sab99r/Indian-States-And-Districts/master/states-and-districts.json'")
        return False

    # Read JSON
    print(f"📖 Reading data from: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    states_data = data.get('states', [])
    total_districts = sum(len(state.get('districts', [])) for state in states_data)

    print(f"✅ Found {len(states_data)} states")
    print(f"✅ Found {total_districts} total districts\n")

    # Connect to database
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear existing district data
        print("🗑️ Clearing existing district data...")
        session.execute(text("TRUNCATE TABLE admin_panchayats, admin_blocks, admin_districts CASCADE"))
        session.commit()
        print("✅ Cleared old data\n")

        # State code mapping (from our existing admin_states table)
        state_code_map = {
            "Andaman and Nicobar Islands": "35",
            "Andhra Pradesh": "28",
            "Arunachal Pradesh": "12",
            "Assam": "18",
            "Bihar": "10",
            "Chandigarh": "04",
            "Chhattisgarh": "22",
            "Dadra and Nagar Haveli": "26",
            "Daman and Diu": "25",
            "Delhi": "07",
            "Goa": "30",
            "Gujarat": "24",
            "Haryana": "06",
            "Himachal Pradesh": "02",
            "Jammu and Kashmir": "01",
            "Jharkhand": "20",
            "Karnataka": "29",
            "Kerala": "32",
            "Ladakh": "37",
            "Lakshadweep": "31",
            "Madhya Pradesh": "23",
            "Maharashtra": "27",
            "Manipur": "14",
            "Meghalaya": "17",
            "Mizoram": "15",
            "Nagaland": "13",
            "Odisha": "21",
            "Puducherry": "34",
            "Punjab": "03",
            "Rajasthan": "08",
            "Sikkim": "11",
            "Tamil Nadu": "33",
            "Telangana": "36",
            "Tripura": "16",
            "Uttar Pradesh": "09",
            "Uttarakhand": "05",
            "West Bengal": "19",
        }

        # Import districts
        print("💾 Importing districts...")
        imported_count = 0
        lgd_code_counter = 1000  # Start LGD codes from 1000

        for state in states_data:
            state_name = state.get('state', '')
            state_code = state_code_map.get(state_name)

            if not state_code:
                print(f"⚠️ No state code mapping for: {state_name}")
                continue

            districts = state.get('districts', [])

            for district in districts:
                try:
                    # Use district name as-is (English)
                    # For Hindi, we'll use transliteration or leave blank for now
                    district_data = {
                        "name": district,  # Will add Hindi translation later
                        "name_en": district,
                        "lgd_code": str(lgd_code_counter),
                        "state_code": state_code
                    }

                    session.execute(
                        text("""
                            INSERT INTO admin_districts (name, name_en, lgd_code, state_code)
                            VALUES (:name, :name_en, :lgd_code, :state_code)
                            ON CONFLICT (lgd_code) DO NOTHING
                        """),
                        district_data
                    )

                    imported_count += 1
                    lgd_code_counter += 1

                    if imported_count % 100 == 0:
                        session.commit()
                        print(f"  ... imported {imported_count} districts")

                except Exception as e:
                    print(f"⚠️ Error importing district '{district}' for state '{state_name}': {e}")
                    continue

        session.commit()
        print(f"\n✅ Successfully imported {imported_count} districts!")

        # Verify counts
        result = session.execute(text("SELECT COUNT(*) FROM admin_districts")).fetchone()
        print(f"📊 Total districts in database: {result[0]}")

        # Show distribution by state
        print("\n📊 Districts by state (top 10):")
        result = session.execute(text("""
            SELECT s.name_en, COUNT(d.id) as district_count
            FROM admin_states s
            LEFT JOIN admin_districts d ON s.state_code = d.state_code
            GROUP BY s.name_en, s.state_code
            ORDER BY district_count DESC
            LIMIT 10
        """)).fetchall()

        for state_name, count in result:
            print(f"   {state_name}: {count} districts")

        return True

    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    try:
        success = import_districts_from_json()
        if success:
            print("\n🎉 District import completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ District import failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
