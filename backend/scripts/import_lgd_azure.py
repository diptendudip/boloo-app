#!/usr/bin/env python3
"""
LGD Data Import Script for Azure PostgreSQL
Imports states and districts data from JSON into Azure PostgreSQL database

Usage:
  # Set Azure DATABASE_URL environment variable first:
  export DATABASE_URL="postgresql://user:password@host:5432/dbname"
  python3 scripts/import_lgd_azure.py

  # Or provide it inline:
  DATABASE_URL="postgresql://..." python3 scripts/import_lgd_azure.py
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment or config"""
    # Try environment variable first (Azure setting)
    db_url = os.environ.get('DATABASE_URL')

    if not db_url:
        # Try loading from .env for local testing
        try:
            from app.config import settings
            db_url = settings.DATABASE_URL
            logger.info("Using DATABASE_URL from app config")
        except Exception as e:
            logger.error(f"Could not load config: {e}")
            return None

    # Validate database URL
    if not db_url or not db_url.startswith('postgresql'):
        logger.error(f"Invalid DATABASE_URL: {db_url}")
        logger.error("Please set DATABASE_URL environment variable")
        logger.error("Example: export DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
        return None

    # Mask password for logging
    if '@' in db_url:
        masked_url = db_url.split('@')[1]
        logger.info(f"Database: {masked_url}")
    else:
        logger.info(f"Database: {db_url}")

    return db_url


def create_connection(db_url):
    """Create database engine and session"""
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=False,
            connect_args={
                'connect_timeout': 30,
                'options': '-c statement_timeout=300000'  # 5 minutes
            }
        )

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return engine, SessionLocal

    except Exception as e:
        logger.error(f"Failed to create database connection: {e}")
        raise


def load_json_data():
    """Load states and districts from JSON file"""
    json_path = Path(__file__).parent.parent / "data" / "lgd" / "states-districts.json"

    logger.info(f"Loading data from: {json_path}")

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data['states'])} states from JSON")
    return data


def create_tables_if_not_exist(db):
    """Create admin tables if they don't exist"""

    # Check if tables exist
    check_states_table = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'admin_states'
        );
    """)

    check_districts_table = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'admin_districts'
        );
    """)

    states_exists = db.execute(check_states_table).scalar()
    districts_exists = db.execute(check_districts_table).scalar()

    logger.info(f"Tables exist - States: {states_exists}, Districts: {districts_exists}")

    if not states_exists:
        logger.info("Creating admin_states table...")
        create_states = text("""
            CREATE TABLE admin_states (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                name_en VARCHAR(255) NOT NULL,
                state_code VARCHAR(10) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        db.execute(create_states)
        db.commit()
        logger.info("admin_states table created")

    if not districts_exists:
        logger.info("Creating admin_districts table...")
        create_districts = text("""
            CREATE TABLE admin_districts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                name_en VARCHAR(255) NOT NULL,
                lgd_code VARCHAR(10),
                state_code VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (state_code) REFERENCES admin_states(state_code) ON DELETE CASCADE
            );
        """)
        db.execute(create_districts)
        db.commit()
        logger.info("admin_districts table created")

    # Create indexes
    if not states_exists:
        try:
            create_state_index = text("CREATE INDEX IF NOT EXISTS idx_states_code ON admin_states(state_code);")
            db.execute(create_state_index)
            db.commit()
        except Exception as e:
            logger.warning(f"Could not create state index: {e}")

    if not districts_exists:
        try:
            create_district_index = text("CREATE INDEX IF NOT EXISTS idx_districts_state_code ON admin_districts(state_code);")
            db.execute(create_district_index)
            db.commit()
        except Exception as e:
            logger.warning(f"Could not create district index: {e}")


def get_state_code(state_name):
    """Generate state code from state name (standard Indian state codes)"""
    # Standard Indian state codes (as per Census of India)
    state_codes = {
        "Andhra Pradesh": "28",
        "Arunachal Pradesh": "12",
        "Assam": "18",
        "Bihar": "10",
        "Chhattisgarh": "22",
        "Goa": "30",
        "Gujarat": "24",
        "Haryana": "06",
        "Himachal Pradesh": "02",
        "Jharkhand": "20",
        "Karnataka": "29",
        "Kerala": "32",
        "Madhya Pradesh": "23",
        "Maharashtra": "27",
        "Manipur": "14",
        "Meghalaya": "17",
        "Mizoram": "15",
        "Nagaland": "13",
        "Odisha": "21",
        "Punjab": "03",
        "Rajasthan": "08",
        "Sikkim": "11",
        "Tamil Nadu": "33",
        "Telangana": "36",
        "Tripura": "16",
        "Uttar Pradesh": "09",
        "Uttarakhand": "05",
        "West Bengal": "19",
        "Andaman and Nicobar Islands": "35",
        "Chandigarh": "04",
        "Dadra and Nagar Haveli and Daman and Diu": "26",
        "Delhi": "07",
        "Jammu and Kashmir": "01",
        "Ladakh": "37",
        "Lakshadweep": "31",
        "Puducherry": "34"
    }

    return state_codes.get(state_name, str(hash(state_name) % 100).zfill(2))


def import_states(db, states_data):
    """Import states into database"""
    logger.info("Importing states...")

    # Clear existing data
    logger.info("Clearing existing data...")
    clear_districts = text("DELETE FROM admin_districts;")
    clear_states = text("DELETE FROM admin_states;")

    db.execute(clear_districts)
    db.execute(clear_states)
    db.commit()

    logger.info("Cleared existing data")

    imported_count = 0
    state_code_map = {}

    for state_data in states_data:
        state_name = state_data['state']
        state_code = get_state_code(state_name)
        state_code_map[state_name] = state_code

        # Insert state
        insert_query = text("""
            INSERT INTO admin_states (name, name_en, state_code)
            VALUES (:name, :name_en, :state_code)
            ON CONFLICT (state_code) DO NOTHING
        """)

        db.execute(insert_query, {
            "name": state_name,
            "name_en": state_name,
            "state_code": state_code
        })

        imported_count += 1

    db.commit()
    logger.info(f"Imported {imported_count} states")

    return state_code_map


def import_districts(db, states_data, state_code_map):
    """Import districts into database"""
    logger.info("Importing districts...")

    imported_count = 0

    for state_data in states_data:
        state_name = state_data['state']
        state_code = state_code_map.get(state_name)

        if not state_code:
            logger.warning(f"No state code found for: {state_name}")
            continue

        for district_name in state_data['districts']:
            # Generate a simple LGD code (can be replaced with actual codes if available)
            lgd_code = f"{state_code}{str(hash(district_name) % 1000).zfill(3)}"

            insert_query = text("""
                INSERT INTO admin_districts (name, name_en, lgd_code, state_code)
                VALUES (:name, :name_en, :lgd_code, :state_code)
            """)

            db.execute(insert_query, {
                "name": district_name,
                "name_en": district_name,
                "lgd_code": lgd_code,
                "state_code": state_code
            })

            imported_count += 1

    db.commit()
    logger.info(f"Imported {imported_count} districts")

    return imported_count


def verify_import(db):
    """Verify the imported data"""
    logger.info("Verifying import...")

    # Count states
    states_count = db.execute(text("SELECT COUNT(*) FROM admin_states")).scalar()
    logger.info(f"Total states in database: {states_count}")

    # Count districts
    districts_count = db.execute(text("SELECT COUNT(*) FROM admin_districts")).scalar()
    logger.info(f"Total districts in database: {districts_count}")

    # Sample some states
    sample_states = db.execute(text("""
        SELECT id, name_en, state_code
        FROM admin_states
        ORDER BY name_en
        LIMIT 5
    """)).fetchall()

    logger.info("\nSample states:")
    for state in sample_states:
        logger.info(f"  - {state[1]} (code: {state[2]})")

    # Sample some districts
    sample_districts = db.execute(text("""
        SELECT d.name_en, d.state_code, s.name_en as state_name
        FROM admin_districts d
        JOIN admin_states s ON d.state_code = s.state_code
        ORDER BY d.name_en
        LIMIT 5
    """)).fetchall()

    logger.info("\nSample districts:")
    for district in sample_districts:
        logger.info(f"  - {district[0]} ({district[2]})")

    return states_count, districts_count


def main():
    """Main import function"""
    logger.info("=" * 80)
    logger.info("LGD Data Import Script for Azure PostgreSQL")
    logger.info("=" * 80)

    # Get database URL
    db_url = get_database_url()
    if not db_url:
        logger.error("Failed to get database URL. Exiting.")
        return False

    # Create connection
    try:
        engine, SessionLocal = create_connection(db_url)
        db = SessionLocal()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return False

    try:
        # Load JSON data
        data = load_json_data()

        # Create tables if needed
        create_tables_if_not_exist(db)

        # Import states
        state_code_map = import_states(db, data['states'])

        # Import districts
        import_districts(db, data['states'], state_code_map)

        # Verify import
        states_count, districts_count = verify_import(db)

        logger.info("")
        logger.info("=" * 80)
        logger.info("Import completed successfully!")
        logger.info(f"Imported {states_count} states and {districts_count} districts")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
