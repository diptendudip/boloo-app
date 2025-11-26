#!/usr/bin/env python3
"""
LGD (Local Government Directory) Data Importer
Imports hierarchical administrative unit data into the database.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
import re

import pandas as pd
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lgd_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LGDDataImporter:
    """Import LGD administrative unit data into database."""

    # LGD state code for Chhattisgarh
    CHHATTISGARH_STATE_CODE = "22"

    # Administrative level hierarchy
    LEVELS = {
        'state': 1,
        'district': 2,
        'block': 3,
        'panchayat': 4,
        'village': 5
    }

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize importer with database connection.

        Args:
            database_url: PostgreSQL connection URL. If None, reads from environment.
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/boloo_dev'
        )
        self.engine = create_engine(self.database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        logger.info(f"Connected to database: {self.database_url}")

    def download_excel_data(self, url: str, output_path: str) -> bool:
        """
        Download LGD Excel file from URL.

        Args:
            url: URL of the Excel/CSV file
            output_path: Local path to save the file

        Returns:
            True if download successful, False otherwise
        """
        try:
            logger.info(f"Downloading data from {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Create directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Downloaded to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False

    def parse_excel_file(self, file_path: str, level: str) -> List[Dict]:
        """
        Parse Excel/CSV file into structured data.

        Args:
            file_path: Path to the Excel/CSV file
            level: Administrative level (state, district, block, panchayat, village)

        Returns:
            List of dictionaries containing parsed data
        """
        try:
            logger.info(f"Parsing {file_path} for level: {level}")

            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path)

            # Clean column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            data = []
            for _, row in df.iterrows():
                record = self._parse_row(row, level)
                if record:
                    data.append(record)

            logger.info(f"Parsed {len(data)} records from {file_path}")
            return data

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []

    def _parse_row(self, row: pd.Series, level: str) -> Optional[Dict]:
        """
        Parse a single row from the Excel file.

        Args:
            row: Pandas Series representing a row
            level: Administrative level

        Returns:
            Dictionary with parsed data or None if invalid
        """
        try:
            # Common fields
            record = {
                'lgd_code': str(row.get('lgd_code', '')).strip(),
                'name_english': str(row.get('name', '')).strip(),
                'name_hindi': str(row.get('name_hindi', '')).strip(),
                'level': self.LEVELS.get(level, 0),
                'is_active': True
            }

            # Level-specific parent codes
            if level == 'district':
                record['state_code'] = self.CHHATTISGARH_STATE_CODE
            elif level == 'block':
                record['state_code'] = self.CHHATTISGARH_STATE_CODE
                record['district_code'] = str(row.get('district_code', '')).strip()
            elif level == 'panchayat':
                record['state_code'] = self.CHHATTISGARH_STATE_CODE
                record['district_code'] = str(row.get('district_code', '')).strip()
                record['block_code'] = str(row.get('block_code', '')).strip()
            elif level == 'village':
                record['state_code'] = self.CHHATTISGARH_STATE_CODE
                record['district_code'] = str(row.get('district_code', '')).strip()
                record['block_code'] = str(row.get('block_code', '')).strip()
                record['panchayat_code'] = str(row.get('panchayat_code', '')).strip()

            # Additional metadata
            if 'census_code' in row:
                record['census_code'] = str(row['census_code']).strip()

            if 'population' in row:
                try:
                    record['population'] = int(row['population'])
                except (ValueError, TypeError):
                    record['population'] = None

            # Validate required fields
            if not record['lgd_code'] or not record['name_english']:
                logger.warning(f"Skipping invalid row: {row.to_dict()}")
                return None

            return record

        except Exception as e:
            logger.error(f"Error parsing row: {e}")
            return None

    def build_name_aliases(self, name_english: str, name_hindi: Optional[str] = None) -> List[str]:
        """
        Generate name aliases for fuzzy matching.

        Args:
            name_english: English name
            name_hindi: Hindi name (optional)

        Returns:
            List of name variations and aliases
        """
        aliases: Set[str] = set()

        # Original name
        aliases.add(name_english.lower())

        # Remove common suffixes
        for suffix in ['district', 'block', 'gram panchayat', 'tehsil', 'taluka']:
            if name_english.lower().endswith(suffix):
                base_name = name_english[:-len(suffix)].strip()
                aliases.add(base_name.lower())

        # Common variations
        if name_hindi:
            aliases.add(name_hindi.lower())

        # Handle special cases for Chhattisgarh
        cg_aliases = {
            'chhattisgarh': ['cg', 'chattisgarh', 'chhatisgarh', 'छत्तीसगढ़'],
            'raipur': ['raypur', 'रायपुर'],
            'bilaspur': ['bilaspur', 'बिलासपुर'],
            'durg': ['durga', 'दुर्ग'],
            'rajnandgaon': ['rajnandgaon', 'raj nandgaon', 'राजनांदगांव'],
            'bastar': ['baster', 'बस्तर'],
            'kondagaon': ['kondagaon', 'कोंडागांव'],
            'kanker': ['kanker', 'कांकेर'],
            'surguja': ['sarguja', 'सरगुजा'],
            'jashpur': ['jashpur', 'जशपुर'],
            'korba': ['korba', 'कोरबा'],
            'raigarh': ['raigarh', 'रायगढ़'],
            'janjgir': ['janjgir-champa', 'janjgir champa', 'जांजगीर-चांपा']
        }

        name_lower = name_english.lower()
        for key, variations in cg_aliases.items():
            if key in name_lower:
                aliases.update(variations)

        # Remove duplicates and empty strings
        aliases = {a.strip() for a in aliases if a and a.strip()}

        return sorted(list(aliases))

    def import_to_database(self, data: List[Dict]) -> int:
        """
        Insert data into lgd_admin_units table.

        Args:
            data: List of dictionaries containing admin unit data

        Returns:
            Number of records successfully imported
        """
        imported_count = 0

        try:
            for record in data:
                try:
                    # Generate aliases
                    aliases = self.build_name_aliases(
                        record['name_english'],
                        record.get('name_hindi')
                    )
                    record['name_aliases'] = aliases

                    # Prepare SQL
                    columns = ', '.join(record.keys())
                    placeholders = ', '.join([f':{k}' for k in record.keys()])

                    sql = f"""
                        INSERT INTO lgd_admin_units ({columns})
                        VALUES ({placeholders})
                        ON CONFLICT (lgd_code) DO UPDATE SET
                            name_english = EXCLUDED.name_english,
                            name_hindi = EXCLUDED.name_hindi,
                            name_aliases = EXCLUDED.name_aliases,
                            is_active = EXCLUDED.is_active,
                            updated_at = NOW()
                    """

                    self.session.execute(text(sql), record)
                    imported_count += 1

                    if imported_count % 100 == 0:
                        self.session.commit()
                        logger.info(f"Imported {imported_count} records...")

                except IntegrityError as e:
                    logger.warning(f"Duplicate or integrity error for {record.get('lgd_code')}: {e}")
                    self.session.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Error importing record {record.get('lgd_code')}: {e}")
                    self.session.rollback()
                    continue

            # Final commit
            self.session.commit()
            logger.info(f"Successfully imported {imported_count} records")
            return imported_count

        except Exception as e:
            logger.error(f"Failed to import data: {e}")
            self.session.rollback()
            return imported_count

    def import_chhattisgarh_data(self, data_dir: str = './data/lgd', level: str = 'all') -> Dict[str, int]:
        """
        Main function to import all Chhattisgarh data.

        Args:
            data_dir: Directory containing Excel/CSV files
            level: Level to import ('all', 'district', 'block', 'panchayat', 'village')

        Returns:
            Dictionary with import statistics per level
        """
        stats = {}
        data_path = Path(data_dir)

        # Import in hierarchical order
        levels_to_import = ['state', 'district', 'block', 'panchayat', 'village']

        if level != 'all':
            if level not in levels_to_import:
                logger.error(f"Invalid level: {level}")
                return stats
            # Import from state level to requested level
            idx = levels_to_import.index(level)
            levels_to_import = levels_to_import[:idx + 1]

        for admin_level in levels_to_import:
            logger.info(f"\n{'='*50}")
            logger.info(f"Importing {admin_level} level data")
            logger.info(f"{'='*50}")

            # Look for files matching the level
            patterns = [
                f"*{admin_level}*.xlsx",
                f"*{admin_level}*.csv",
                f"chhattisgarh_{admin_level}*.xlsx",
                f"chhattisgarh_{admin_level}*.csv",
                f"22_{admin_level}*.xlsx",  # State code prefix
                f"22_{admin_level}*.csv"
            ]

            files_found = []
            for pattern in patterns:
                files_found.extend(list(data_path.glob(pattern)))

            if not files_found:
                logger.warning(f"No files found for {admin_level} level in {data_dir}")
                stats[admin_level] = 0
                continue

            total_imported = 0
            for file_path in files_found:
                logger.info(f"Processing {file_path.name}")
                data = self.parse_excel_file(str(file_path), admin_level)
                if data:
                    count = self.import_to_database(data)
                    total_imported += count

            stats[admin_level] = total_imported

        # Log summary
        logger.info(f"\n{'='*50}")
        logger.info("Import Summary")
        logger.info(f"{'='*50}")
        for level, count in stats.items():
            logger.info(f"{level.capitalize()}: {count} records")

        return stats

    def import_district_data(self, district_name: str, level: str = 'village') -> Dict[str, int]:
        """
        Import data for a specific district.

        Args:
            district_name: Name of the district
            level: Deepest level to import

        Returns:
            Dictionary with import statistics
        """
        logger.info(f"Importing data for {district_name} district up to {level} level")

        # First, find the district code
        sql = """
            SELECT lgd_code FROM lgd_admin_units
            WHERE level = 2
            AND (LOWER(name_english) = LOWER(:name)
                 OR :name = ANY(name_aliases))
        """
        result = self.session.execute(text(sql), {'name': district_name.lower()}).fetchone()

        if not result:
            logger.error(f"District not found: {district_name}")
            return {}

        district_code = result[0]
        logger.info(f"Found district code: {district_code}")

        # Import data for this district
        # This would need district-specific Excel files
        # Implementation depends on LGD data structure

        return {}

    def close(self):
        """Close database connection."""
        self.session.close()
        self.engine.dispose()
        logger.info("Database connection closed")


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Import LGD administrative unit data into database'
    )
    parser.add_argument(
        '--state',
        default='chhattisgarh',
        help='State to import (default: chhattisgarh)'
    )
    parser.add_argument(
        '--level',
        choices=['all', 'district', 'block', 'panchayat', 'village'],
        default='all',
        help='Level to import (default: all)'
    )
    parser.add_argument(
        '--district',
        help='Specific district to import'
    )
    parser.add_argument(
        '--data-dir',
        default='./data/lgd',
        help='Directory containing LGD Excel/CSV files (default: ./data/lgd)'
    )
    parser.add_argument(
        '--database-url',
        help='PostgreSQL connection URL (default: from DATABASE_URL env)'
    )
    parser.add_argument(
        '--download',
        help='Download data from URL before importing'
    )

    args = parser.parse_args()

    try:
        # Initialize importer
        importer = LGDDataImporter(database_url=args.database_url)

        # Download data if URL provided
        if args.download:
            output_path = os.path.join(args.data_dir, 'downloaded_data.xlsx')
            if not importer.download_excel_data(args.download, output_path):
                logger.error("Failed to download data")
                return 1

        # Import data
        if args.district:
            stats = importer.import_district_data(args.district, args.level)
        else:
            stats = importer.import_chhattisgarh_data(args.data_dir, args.level)

        # Close connection
        importer.close()

        # Print summary
        print(f"\n{'='*50}")
        print("Import completed successfully!")
        print(f"{'='*50}")
        for level, count in stats.items():
            print(f"{level.capitalize()}: {count} records")

        return 0

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
