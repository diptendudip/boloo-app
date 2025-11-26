#!/usr/bin/env python3
"""
Import Blocks and Panchayats from Census 2011 Data
Imports sub-district (block) and village/panchayat data for 6 major states
"""

import pandas as pd
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


def import_census_data():
    """Import blocks and panchayats from Census 2011 files"""

    print("\n" + "="*70)
    print("🇮🇳 IMPORTING BLOCKS & PANCHAYATS FROM CENSUS 2011 DATA")
    print("="*70 + "\n")

    # File mappings
    census_files = [
        ('/Users/diptendu/Downloads/Rdir_2011_10_BIHAR.xls', 'Bihar', '10'),
        ('/Users/diptendu/Downloads/Rdir_2011_22_CHHATTISGARH.xls', 'Chhattisgarh', '22'),
        ('/Users/diptendu/Downloads/Rdir_2011_20_JHARKHAND.xls', 'Jharkhand', '20'),
        ('/Users/diptendu/Downloads/Rdir_2011_23_MADHYA_PRADESH.xls', 'Madhya Pradesh', '23'),
        ('/Users/diptendu/Downloads/Rdir_2011_27_MAHARASHTRA.xls', 'Maharashtra', '27'),
        ('/Users/diptendu/Downloads/Rdir_2011_09_UTTAR_PRADESH.ods', 'Uttar Pradesh', '09'),
    ]

    # Connect to database
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get existing district mappings
        print("📍 Loading district mappings from database...")
        district_map = {}
        result = session.execute(text("""
            SELECT name_en, lgd_code, state_code
            FROM admin_districts
        """)).fetchall()

        for district_name, lgd_code, state_code in result:
            key = (state_code, district_name.strip().upper())
            district_map[key] = lgd_code

        print(f"✅ Loaded {len(district_map)} district mappings\n")

        total_blocks_imported = 0
        total_panchayats_imported = 0
        block_lgd_counter = 10000  # Start LGD codes for blocks
        panchayat_lgd_counter = 100000  # Start LGD codes for panchayats

        for file_path, state_name, state_code in census_files:
            if not Path(file_path).exists():
                print(f"⚠️ File not found: {file_path}")
                continue

            print(f"📖 Processing {state_name}...")

            try:
                # Read Excel/ODS file
                if file_path.endswith('.ods'):
                    df = pd.read_excel(file_path, engine='odf')
                else:
                    df = pd.read_excel(file_path)

                print(f"   Total rows: {len(df):,}")

                # Extract blocks (sub-districts where MDDS PLCN == 0 and MDDS Sub_DT > 0)
                blocks_df = df[(df['MDDS Sub_DT'] > 0) & (df['MDDS PLCN'] == 0)].copy()
                print(f"   Blocks found: {len(blocks_df)}")

                # Extract panchayats/villages (where MDDS PLCN > 0)
                panchayats_df = df[df['MDDS PLCN'] > 0].copy()
                print(f"   Panchayats found: {len(panchayats_df):,}")

                # Import blocks
                blocks_imported = 0
                for _, row in blocks_df.iterrows():
                    try:
                        district_name = str(row['DISTRICT NAME']).strip().upper()
                        district_key = (state_code, district_name)

                        if district_key not in district_map:
                            # Try alternative matching
                            for (s_code, d_name), lgd in district_map.items():
                                if s_code == state_code and district_name in d_name:
                                    district_key = (s_code, d_name)
                                    break

                        if district_key in district_map:
                            district_lgd = district_map[district_key]

                            block_data = {
                                "name": str(row['SUB-DISTRICT NAME']).strip(),
                                "name_en": str(row['SUB-DISTRICT NAME']).strip(),
                                "lgd_code": str(block_lgd_counter),
                                "district_lgd_code": district_lgd
                            }

                            session.execute(
                                text("""
                                    INSERT INTO admin_blocks (name, name_en, lgd_code, district_lgd_code)
                                    VALUES (:name, :name_en, :lgd_code, :district_lgd_code)
                                    ON CONFLICT (lgd_code) DO NOTHING
                                """),
                                block_data
                            )

                            blocks_imported += 1
                            block_lgd_counter += 1

                    except Exception as e:
                        continue

                session.commit()
                total_blocks_imported += blocks_imported
                print(f"   ✅ Imported {blocks_imported} blocks")

                # Import panchayats (limit to reasonable number to avoid overwhelming)
                panchayats_imported = 0
                for _, row in panchayats_df.head(5000).iterrows():  # Limit per state
                    try:
                        # Get block LGD code - we'll need to match it
                        subdistrict_name = str(row['SUB-DISTRICT NAME']).strip()

                        # Find block LGD code from database
                        block_result = session.execute(
                            text("""
                                SELECT lgd_code FROM admin_blocks
                                WHERE name_en = :name
                                LIMIT 1
                            """),
                            {"name": subdistrict_name}
                        ).fetchone()

                        if block_result:
                            block_lgd = block_result[0]

                            panchayat_data = {
                                "name": str(row['Area Name']).strip(),
                                "name_en": str(row['Area Name']).strip(),
                                "lgd_code": str(panchayat_lgd_counter),
                                "block_lgd_code": block_lgd
                            }

                            session.execute(
                                text("""
                                    INSERT INTO admin_panchayats (name, name_en, lgd_code, block_lgd_code)
                                    VALUES (:name, :name_en, :lgd_code, :block_lgd_code)
                                    ON CONFLICT (lgd_code) DO NOTHING
                                """),
                                panchayat_data
                            )

                            panchayats_imported += 1
                            panchayat_lgd_counter += 1

                            if panchayats_imported % 1000 == 0:
                                session.commit()

                    except Exception as e:
                        continue

                session.commit()
                total_panchayats_imported += panchayats_imported
                print(f"   ✅ Imported {panchayats_imported} panchayats\n")

            except Exception as e:
                print(f"   ❌ Error processing {state_name}: {e}\n")
                continue

        print("="*70)
        print(f"✅ IMPORT SUMMARY:")
        print(f"   Total Blocks Imported: {total_blocks_imported}")
        print(f"   Total Panchayats Imported: {total_panchayats_imported}")

        # Verify counts
        blocks_count = session.execute(text("SELECT COUNT(*) FROM admin_blocks")).fetchone()[0]
        panchayats_count = session.execute(text("SELECT COUNT(*) FROM admin_panchayats")).fetchone()[0]

        print(f"\n📊 DATABASE TOTALS:")
        print(f"   Blocks in database: {blocks_count}")
        print(f"   Panchayats in database: {panchayats_count}")

        return True

    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    try:
        success = import_census_data()
        if success:
            print("\n🎉 Census data import completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Census data import failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
