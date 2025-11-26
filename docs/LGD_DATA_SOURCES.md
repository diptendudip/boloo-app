# LGD (Local Government Directory) Data Sources - Chhattisgarh

## Executive Summary

This document provides comprehensive information about accessing Local Government Directory (LGD) data for Chhattisgarh state, including download methods, data structure, and integration strategies.

**Chhattisgarh State Overview (LGD State Code: 22)**
- **Total Districts**: 33
- **Blocks (Janapad Panchayats)**: 146
- **Gram Panchayats**: 11,664
- **Villages**: 19,567
- **District Panchayats**: 27

## Table of Contents
1. [Official Data Sources](#official-data-sources)
2. [Download Options](#download-options)
3. [Data Structure & Fields](#data-structure--fields)
4. [Step-by-Step Download Process](#step-by-step-download-process)
5. [API Access](#api-access)
6. [Import Strategy](#import-strategy)
7. [Sample Data](#sample-data)
8. [Update Frequency](#update-frequency)

---

## Official Data Sources

### 1. LGD Official Portal (Primary Source)
- **URL**: https://lgdirectory.gov.in/
- **Download Page**: https://lgdirectory.gov.in/downloadDirectory.do
- **Description**: Official government portal maintained under e-Panchayat Mission Mode Project
- **Authority**: Ministry of Panchayati Raj, Government of India
- **Status**: Active, regularly updated

### 2. Open Government Data Platform India
- **URL**: https://data.gov.in/catalog/local-government-directory-lgd
- **Update Frequency**: Updated on 1st day of every month
- **Format**: CSV, Excel
- **Access**: Free, no authentication required

### 3. India Data Portal (CKAN)
- **URL**: https://ckandev.indiadataportal.com/dataset/lgd-codes
- **Direct CSV Downloads**:
  - Districts: https://ckandev.indiadataportal.com/dataset/a7419751-ac37-46ad-b938-638cda7b7b60/resource/19df978a-675e-4ff5-8015-d0e1de447319/download/district-lgd-codes.csv
  - Blocks: https://ckandev.indiadataportal.com/dataset/a7419751-ac37-46ad-b938-638cda7b7b60/resource/bdf22015-a213-4e23-b693-ca40bec4346e/download/block-lgd-codes.csv
  - Gram Panchayats: https://ckandev.indiadataportal.com/dataset/a7419751-ac37-46ad-b938-638cda7b7b60/resource/f49a01ad-180b-4ff5-8015-d0e1de447319/download/gram-panchayat-lgd-codes.csv
  - Villages: https://ckandev.indiadataportal.com/dataset/a7419751-ac37-46ad-b938-638cda7b7b60/resource/cb81a7a4-a3bc-4962-a1eb-838a1db5bfdb/download/villages-lgd-codes.csv

### 4. Community-Maintained CSV Dump
- **URL**: https://ramseraph.github.io/opendata/lgd/
- **Description**: Complete dump of lgdirectory.gov.in in CSV format
- **Update**: Regular updates from official source
- **Special Requirements**: Use 7-Zip for extraction (standard unzip won't work)
- **GitHub Source**: https://github.com/ramSeraph/opendata

### 5. Alternative Community Resource
- **GitHub**: https://github.com/planemad/india-local-government-directory
- **Last Updated**: March 11, 2022
- **License**: Government Open Data License – India
- **Format**: CSV files

---

## Download Options

### Available File Formats
1. **PDF Report** - For viewing and printing
2. **HTML Report** - Web-based viewing
3. **XLS Report** - Microsoft Excel spreadsheet
4. **ODT** - Open Document Text format
5. **CSV** - Comma-separated values (most common for data import)

### Entity Types Available for Download

#### Administrative Units
- All States of India
- All Districts (nationwide or by state)
- All Sub-Districts (nationwide, by state, or by district)
- Development Blocks of India

#### Local Bodies
- Villages (all of India, by state, district, or sub-district)
- PRI Local Bodies (Panchayati Raj Institutions)
- Urban Local Bodies and Wards
- Traditional Local Bodies

#### Mapping Data
- Village to Gram Panchayat Mapping
- Development Blocks with Covered Villages
- Parliament and Assembly Constituency data
- Pincode to Village/Urban mappings

---

## Data Structure & Fields

### District Level Data
**Expected Fields:**
- State Code (e.g., 22 for Chhattisgarh)
- State Name
- District Code (LGD Code)
- District Name
- District Name (Local Language)
- Census 2011 Code
- Status (Active/Inactive)
- Last Updated Date

### Block Level Data
**Expected Fields:**
- State Code
- State Name
- District Code
- District Name
- Block Code (LGD Code)
- Block Name
- Block Name (Local Language)
- Block Type (Rural/Urban)
- Status
- Last Updated Date

### Gram Panchayat Level Data
**Expected Fields:**
- State Code
- District Code
- Block Code
- Gram Panchayat Code (LGD Code)
- Gram Panchayat Name
- Gram Panchayat Name (Local Language)
- Number of Villages Covered
- Status
- Last Updated Date

### Village Level Data
**Expected Fields:**
- State Code
- District Code
- Sub-District Code
- Block Code
- Gram Panchayat Code
- Village Code (LGD Code)
- Village Name
- Village Name (Local Language)
- Village Status (Inhabited/Uninhabited/Forest)
- Census 2011 Code
- PIN Code
- GPS Coordinates (if available)
- Population (Census data)
- Last Updated Date

---

## Step-by-Step Download Process

### Method 1: Official LGD Portal (Web Interface)

**Step 1: Access Download Page**
```
URL: https://lgdirectory.gov.in/downloadDirectory.do
```

**Step 2: Select Download Criteria**
- Choose between:
  - Full directory
  - State-wise entities
  - Modifications-only downloads

**Step 3: Choose Entity Type**
- Select from dropdown:
  - States
  - Districts
  - Sub-Districts
  - Blocks
  - Villages
  - Gram Panchayats
  - Urban Local Bodies

**Step 4: Filter by Geography**
- For Chhattisgarh:
  - Select State: "Chhattisgarh" (Code: 22)
  - Optionally select specific district
  - Optionally select specific block

**Step 5: Select File Format**
- Recommended: **XLS** or **CSV** for data import
- Alternative: PDF for documentation

**Step 6: Complete Captcha**
- Enter security verification text

**Step 7: Generate Report**
- Click "Generate Report" button
- Download will begin automatically

**Step 8: Extract Data**
- Open file in spreadsheet application
- Verify data completeness
- Export as CSV if needed

### Method 2: Direct CSV Download (India Data Portal)

**Step 1: Download All Entity Types**
```bash
# Districts
wget "https://ckandev.indiadataportal.com/dataset/.../district-lgd-codes.csv"

# Blocks
wget "https://ckandev.indiadataportal.com/dataset/.../block-lgd-codes.csv"

# Gram Panchayats
wget "https://ckandev.indiadataportal.com/dataset/.../gram-panchayat-lgd-codes.csv"

# Villages
wget "https://ckandev.indiadataportal.com/dataset/.../villages-lgd-codes.csv"
```

**Step 2: Filter Chhattisgarh Data**
```bash
# Using grep to filter state code 22
grep ",22," district-lgd-codes.csv > chhattisgarh-districts.csv
grep ",22," block-lgd-codes.csv > chhattisgarh-blocks.csv
grep ",22," gram-panchayat-lgd-codes.csv > chhattisgarh-panchayats.csv
grep ",22," villages-lgd-codes.csv > chhattisgarh-villages.csv
```

### Method 3: Community CSV Dump

**Step 1: Visit Archive**
```
URL: https://ramseraph.github.io/opendata/lgd/
```

**Step 2: Select Date**
- Choose from daily archives
- Latest date recommended
- Check "Description" section for data structure

**Step 3: Download Archive**
- Download ZIP file
- **Important**: Use 7-Zip (standard unzip won't work)

**Step 4: Extract Data**
```bash
# Install 7-Zip if not available
# Ubuntu/Debian
sudo apt-get install p7zip-full

# macOS
brew install p7zip

# Extract
7z x lgd-archive-YYYYMMDD.zip
```

**Step 5: Filter for Chhattisgarh**
- Open CSV files
- Filter by State Code = 22

---

## API Access

### NAPIX Web Services

**Base URL**: https://dev.napix.gov.in/nic/lgd/

**Description**: The LGD portal provides web service consumption capabilities through NAPIX API Provider.

**Status**: API endpoints exist but detailed documentation is not publicly available online.

**Expected Capabilities**:
- Retrieve state list
- Retrieve districts by state code
- Retrieve blocks by district code
- Retrieve villages by block code
- Retrieve gram panchayat details

### Potential API Endpoints (To Be Confirmed)

```
GET /api/states
GET /api/districts?stateCode=22
GET /api/blocks?districtCode={code}
GET /api/villages?blockCode={code}
GET /api/grampanchayats?blockCode={code}
```

**Response Format**: Likely JSON

**Authentication**: May require API key or token (contact LGD admin)

**Rate Limits**: Unknown - to be determined

### Alternative: Web Scraping Considerations

If API is unavailable:
- Use Selenium/Puppeteer for web automation
- Parse HTML tables from entity view pages
- Implement rate limiting (1 request per 2 seconds)
- Cache responses to minimize server load
- Consider ethical implications and terms of service

---

## Import Strategy

### Recommended Approach: Phased Import

#### Phase 1: Master Data Setup (One-time)
```sql
-- Create LGD reference tables
CREATE TABLE lgd_states (
  state_code VARCHAR(2) PRIMARY KEY,
  state_name VARCHAR(100),
  state_name_local VARCHAR(100),
  census_code VARCHAR(10),
  status VARCHAR(20),
  last_updated TIMESTAMP
);

CREATE TABLE lgd_districts (
  district_code VARCHAR(10) PRIMARY KEY,
  state_code VARCHAR(2) REFERENCES lgd_states(state_code),
  district_name VARCHAR(100),
  district_name_local VARCHAR(100),
  census_code VARCHAR(10),
  status VARCHAR(20),
  last_updated TIMESTAMP
);

CREATE TABLE lgd_blocks (
  block_code VARCHAR(10) PRIMARY KEY,
  district_code VARCHAR(10) REFERENCES lgd_districts(district_code),
  block_name VARCHAR(100),
  block_name_local VARCHAR(100),
  block_type VARCHAR(20),
  status VARCHAR(20),
  last_updated TIMESTAMP
);

CREATE TABLE lgd_gram_panchayats (
  gp_code VARCHAR(10) PRIMARY KEY,
  block_code VARCHAR(10) REFERENCES lgd_blocks(block_code),
  gp_name VARCHAR(100),
  gp_name_local VARCHAR(100),
  villages_count INTEGER,
  status VARCHAR(20),
  last_updated TIMESTAMP
);

CREATE TABLE lgd_villages (
  village_code VARCHAR(10) PRIMARY KEY,
  gp_code VARCHAR(10) REFERENCES lgd_gram_panchayats(gp_code),
  sub_district_code VARCHAR(10),
  village_name VARCHAR(100),
  village_name_local VARCHAR(100),
  village_status VARCHAR(20),
  census_code VARCHAR(10),
  pin_code VARCHAR(10),
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  population INTEGER,
  status VARCHAR(20),
  last_updated TIMESTAMP
);
```

#### Phase 2: Initial Data Load (Chhattisgarh Only)
```python
import pandas as pd
import psycopg2

# Connect to database
conn = psycopg2.connect(
    dbname="boloo_db",
    user="your_user",
    password="your_password",
    host="localhost"
)

# Load Chhattisgarh districts
districts_df = pd.read_csv('chhattisgarh-districts.csv')
districts_df.to_sql('lgd_districts', conn, if_exists='append', index=False)

# Load blocks
blocks_df = pd.read_csv('chhattisgarh-blocks.csv')
blocks_df.to_sql('lgd_blocks', conn, if_exists='append', index=False)

# Load gram panchayats
gp_df = pd.read_csv('chhattisgarh-panchayats.csv')
gp_df.to_sql('lgd_gram_panchayats', conn, if_exists='append', index=False)

# Load villages
villages_df = pd.read_csv('chhattisgarh-villages.csv')
villages_df.to_sql('lgd_villages', conn, if_exists='append', index=False)

conn.close()
```

#### Phase 3: Incremental Updates (Monthly)
```python
# Download latest data
# Compare with existing data
# Identify changes (new, modified, deleted)
# Update database records

def update_lgd_data():
    # Download latest CSV
    latest_data = download_latest_lgd_data()

    # Load existing data
    existing_data = load_from_database()

    # Find differences
    new_records = latest_data[~latest_data['code'].isin(existing_data['code'])]
    modified_records = identify_modified_records(latest_data, existing_data)
    deleted_records = existing_data[~existing_data['code'].isin(latest_data['code'])]

    # Apply updates
    insert_new_records(new_records)
    update_modified_records(modified_records)
    mark_deleted_records(deleted_records)
```

#### Phase 4: Validation & Quality Checks
```sql
-- Check for orphaned records
SELECT * FROM lgd_villages WHERE gp_code NOT IN (SELECT gp_code FROM lgd_gram_panchayats);

-- Check for duplicate codes
SELECT village_code, COUNT(*) FROM lgd_villages GROUP BY village_code HAVING COUNT(*) > 1;

-- Verify hierarchical integrity
SELECT v.* FROM lgd_villages v
LEFT JOIN lgd_gram_panchayats gp ON v.gp_code = gp.gp_code
LEFT JOIN lgd_blocks b ON gp.block_code = b.block_code
WHERE b.block_code IS NULL;
```

### Integration with Boloo App

**Use Cases:**
1. **User Registration**: Validate village/panchayat during signup
2. **Service Delivery**: Route requests based on administrative boundaries
3. **Analytics**: Generate reports by district/block/panchayat
4. **Notifications**: Send targeted updates to specific geographic areas
5. **Search & Autocomplete**: Provide village/panchayat selection dropdowns

**Implementation Considerations:**
- Create indexed lookup tables for fast searches
- Implement caching for frequently accessed data
- Add full-text search for local language names
- Provide hierarchical dropdowns (State → District → Block → GP → Village)
- Support both English and local language (Hindi/Chhattisgarhi) names

---

## Sample Data

### Chhattisgarh Districts (Sample)
```csv
state_code,state_name,district_code,district_name,census_code,status
22,Chhattisgarh,392,Raipur,22101,Active
22,Chhattisgarh,393,Durg,22102,Active
22,Chhattisgarh,394,Bilaspur,22103,Active
22,Chhattisgarh,395,Bastar,22104,Active
22,Chhattisgarh,396,Rajnandgaon,22105,Active
```

### Expected Data Volumes (Chhattisgarh)
- **Districts**: 33 records (~10 KB)
- **Blocks**: 146 records (~50 KB)
- **Gram Panchayats**: 11,664 records (~5 MB)
- **Villages**: 19,567 records (~15 MB)

**Total Storage**: ~20 MB for complete Chhattisgarh dataset

---

## Update Frequency

### Official LGD Portal
- **Real-time updates**: Changes reflected immediately
- **Bulk updates**: Periodic administrative changes
- **Monitoring**: Check "Recent Changes/Modifications" section
- **State-wise tracking**: Last update date available per state

### Open Government Data Platform
- **Monthly updates**: Updated on 1st day of every month
- **Predictable schedule**: Good for automated sync
- **Versioning**: Each month's data is versioned

### Recommended Sync Strategy
1. **Initial Load**: Full download of all entities
2. **Monthly Refresh**: Download updated data on 2nd of each month
3. **Change Detection**: Compare with existing data to identify deltas
4. **Incremental Updates**: Apply only changed records
5. **Audit Trail**: Maintain history of changes

---

## Authentication & Access Requirements

### Official LGD Portal
- **No authentication required** for data viewing and download
- **Captcha verification** required for each download
- **No API key** needed for web interface
- **Rate limiting**: May apply during bulk downloads

### NAPIX API (If Available)
- **API key required**: Contact LGD administrators
- **Registration process**: Through official channels
- **Usage limits**: To be confirmed
- **Documentation**: Request from Ministry of Panchayati Raj

### Open Government Data Platform
- **No authentication required**
- **Direct download links** work without login
- **No rate limits** observed for reasonable use

---

## Data Quality & Validation

### Known Issues
1. **Special characters**: Local language names may have encoding issues
2. **Duplicate entries**: Rare cases of duplicate LGD codes
3. **Missing coordinates**: GPS data not available for all villages
4. **Census integration**: Some villages may not have Census 2011 mapping
5. **Archive format**: Requires 7-Zip (not standard zip)

### Validation Checklist
- [ ] Verify Chhattisgarh state code is "22"
- [ ] Check total district count matches official count (33)
- [ ] Ensure all blocks have valid district references
- [ ] Validate gram panchayat to block mappings
- [ ] Verify village to panchayat relationships
- [ ] Check for NULL or empty mandatory fields
- [ ] Validate status codes (Active/Inactive)
- [ ] Ensure unique LGD codes across entity types

---

## References & Resources

### Official Documentation
- LGD Portal: https://lgdirectory.gov.in/
- Ministry of Panchayati Raj: https://panchayat.gov.in/en/lgd/
- e-Panchayat Mission: https://panchayat.gov.in/

### Data Sources
- Open Government Data India: https://data.gov.in/
- India Data Portal: https://indiadataportal.com/
- Community CSV Dump: https://ramseraph.github.io/opendata/lgd/

### Technical Resources
- GitHub - Community Mirror: https://github.com/planemad/india-local-government-directory
- GitHub - OpenData Scripts: https://github.com/ramSeraph/opendata
- Wikidata Integration: Synchronization reports available

### Support & Queries
- **Technical Issues**: Contact Ministry of Panchayati Raj
- **Data Accuracy**: Report errors through LGD portal
- **API Access**: Email: lgd[at]nic.in (to be confirmed)

---

## Next Steps for Boloo App Integration

### Immediate Actions
1. **Download Current Data**: Use India Data Portal direct CSV links
2. **Filter Chhattisgarh**: Extract state code 22 records
3. **Create Database Schema**: Implement tables as per import strategy
4. **Initial Load**: Import all 4 entity types (districts, blocks, GPs, villages)
5. **Validation**: Run quality checks on imported data

### Short-term (1-2 weeks)
1. **API Development**: Create REST endpoints for village/panchayat lookup
2. **Search Implementation**: Add autocomplete for village selection
3. **UI Integration**: Update registration/profile forms with LGD data
4. **Testing**: Verify data accuracy with sample villages

### Medium-term (1 month)
1. **Automated Sync**: Schedule monthly data refresh from data.gov.in
2. **Change Detection**: Implement delta processing for updates
3. **Analytics**: Build district/block-wise usage reports
4. **Localization**: Add support for Hindi/Chhattisgarhi names

### Long-term (3 months)
1. **API Integration**: If LGD API becomes available, switch to real-time data
2. **Expansion**: Add support for other states if needed
3. **Advanced Features**: GPS-based village detection, boundary mapping
4. **Data Enrichment**: Integrate Census data, population, demographics

---

**Document Version**: 1.0
**Last Updated**: November 17, 2024
**Author**: Research Agent - Boloo App Development Team
**Status**: Completed - Ready for Implementation

---

## Appendix A: Quick Command Reference

### Download All CSV Files
```bash
# Create download directory
mkdir -p lgd-data

# Download all entity types
curl -o lgd-data/districts.csv "https://ckandev.indiadataportal.com/dataset/a7419751-ac37-46ad-b938-638cda7b7b60/resource/19df978a-675e-4ff5-8015-d0e1de447319/download/district-lgd-codes.csv"

curl -o lgd-data/blocks.csv "https://ckandev.indiadataportal.com/dataset/a7419751-ac37-46ad-b938-638cda7b7b60/resource/bdf22015-a213-4e23-b693-ca40bec4346e/download/block-lgd-codes.csv"

curl -o lgd-data/panchayats.csv "https://ckandev.indiadataportal.com/dataset/a7419751-ac37-46ad-b938-638cda7b7b60/resource/f49a01ad-180b-4ff5-8015-d0e1de447319/download/gram-panchayat-lgd-codes.csv"

curl -o lgd-data/villages.csv "https://ckandev.indiadataportal.com/dataset/a7419751-ac37-46ad-b938-638cda7b7b60/resource/cb81a7a4-a3bc-4962-a1eb-838a1db5bfdb/download/villages-lgd-codes.csv"
```

### Filter Chhattisgarh Data (State Code 22)
```bash
# Extract Chhattisgarh records
grep ",22," lgd-data/districts.csv > lgd-data/chhattisgarh-districts.csv
grep ",22," lgd-data/blocks.csv > lgd-data/chhattisgarh-blocks.csv
grep ",22," lgd-data/panchayats.csv > lgd-data/chhattisgarh-panchayats.csv
grep ",22," lgd-data/villages.csv > lgd-data/chhattisgarh-villages.csv

# Count records
echo "Districts: $(wc -l < lgd-data/chhattisgarh-districts.csv)"
echo "Blocks: $(wc -l < lgd-data/chhattisgarh-blocks.csv)"
echo "Panchayats: $(wc -l < lgd-data/chhattisgarh-panchayats.csv)"
echo "Villages: $(wc -l < lgd-data/chhattisgarh-villages.csv)"
```

---

## Appendix B: Database Import Script

```python
#!/usr/bin/env python3
"""
LGD Data Import Script for Boloo App
Imports Chhattisgarh administrative data from CSV files
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'dbname': 'boloo_db',
    'user': 'boloo_user',
    'password': 'your_password',
    'host': 'localhost',
    'port': 5432
}

# File paths
DATA_DIR = './lgd-data'
FILES = {
    'districts': f'{DATA_DIR}/chhattisgarh-districts.csv',
    'blocks': f'{DATA_DIR}/chhattisgarh-blocks.csv',
    'panchayats': f'{DATA_DIR}/chhattisgarh-panchayats.csv',
    'villages': f'{DATA_DIR}/chhattisgarh-villages.csv'
}

def create_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise

def import_districts(conn, file_path):
    """Import district data"""
    logger.info("Importing districts...")
    df = pd.read_csv(file_path)

    cursor = conn.cursor()
    query = """
        INSERT INTO lgd_districts
        (district_code, state_code, district_name, district_name_local,
         census_code, status, last_updated)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (district_code) DO UPDATE SET
            district_name = EXCLUDED.district_name,
            last_updated = EXCLUDED.last_updated
    """

    data = [
        (row['district_code'], row['state_code'], row['district_name'],
         row.get('district_name_local', ''), row.get('census_code', ''),
         row.get('status', 'Active'), datetime.now())
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, query, data)
    conn.commit()
    logger.info(f"Imported {len(data)} districts")

def import_blocks(conn, file_path):
    """Import block data"""
    logger.info("Importing blocks...")
    df = pd.read_csv(file_path)

    cursor = conn.cursor()
    query = """
        INSERT INTO lgd_blocks
        (block_code, district_code, block_name, block_name_local,
         block_type, status, last_updated)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (block_code) DO UPDATE SET
            block_name = EXCLUDED.block_name,
            last_updated = EXCLUDED.last_updated
    """

    data = [
        (row['block_code'], row['district_code'], row['block_name'],
         row.get('block_name_local', ''), row.get('block_type', 'Rural'),
         row.get('status', 'Active'), datetime.now())
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, query, data)
    conn.commit()
    logger.info(f"Imported {len(data)} blocks")

def import_gram_panchayats(conn, file_path):
    """Import gram panchayat data"""
    logger.info("Importing gram panchayats...")
    df = pd.read_csv(file_path)

    cursor = conn.cursor()
    query = """
        INSERT INTO lgd_gram_panchayats
        (gp_code, block_code, gp_name, gp_name_local,
         villages_count, status, last_updated)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (gp_code) DO UPDATE SET
            gp_name = EXCLUDED.gp_name,
            last_updated = EXCLUDED.last_updated
    """

    data = [
        (row['gp_code'], row['block_code'], row['gp_name'],
         row.get('gp_name_local', ''), row.get('villages_count', 0),
         row.get('status', 'Active'), datetime.now())
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, query, data)
    conn.commit()
    logger.info(f"Imported {len(data)} gram panchayats")

def import_villages(conn, file_path):
    """Import village data"""
    logger.info("Importing villages...")
    df = pd.read_csv(file_path)

    cursor = conn.cursor()
    query = """
        INSERT INTO lgd_villages
        (village_code, gp_code, sub_district_code, village_name,
         village_name_local, village_status, census_code, pin_code,
         latitude, longitude, population, status, last_updated)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (village_code) DO UPDATE SET
            village_name = EXCLUDED.village_name,
            last_updated = EXCLUDED.last_updated
    """

    data = [
        (row['village_code'], row['gp_code'], row.get('sub_district_code', ''),
         row['village_name'], row.get('village_name_local', ''),
         row.get('village_status', 'Inhabited'), row.get('census_code', ''),
         row.get('pin_code', ''), row.get('latitude'), row.get('longitude'),
         row.get('population', 0), row.get('status', 'Active'), datetime.now())
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, query, data)
    conn.commit()
    logger.info(f"Imported {len(data)} villages")

def main():
    """Main import function"""
    try:
        conn = create_connection()

        # Import in hierarchical order
        import_districts(conn, FILES['districts'])
        import_blocks(conn, FILES['blocks'])
        import_gram_panchayats(conn, FILES['panchayats'])
        import_villages(conn, FILES['villages'])

        conn.close()
        logger.info("Import completed successfully")

    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise

if __name__ == '__main__':
    main()
```

---

**End of Document**
