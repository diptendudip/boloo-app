#!/usr/bin/env python3
"""
Script to create database schema from SQLAlchemy models
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.database import Base
from app import models  # Import all models

def main():
    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    print(f"Connecting to database...")
    print(f"URL: {database_url[:50]}...")

    # Create engine
    engine = create_engine(database_url, echo=False)

    print("\nCreating all tables from SQLAlchemy models...")
    Base.metadata.create_all(bind=engine)

    print("✓ All tables created successfully!")

    # List created tables
    import psycopg2
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    AND table_name != 'spatial_ref_sys'
    ORDER BY table_name;
    """)
    tables = cur.fetchall()

    print(f"\n✓ Created {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")

    cur.close()
    conn.close()

    print("\n✓ Schema creation complete!")

if __name__ == "__main__":
    main()
