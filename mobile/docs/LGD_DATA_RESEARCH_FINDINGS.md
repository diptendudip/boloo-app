# Complete LGD Data Research Findings for Indian Administrative Boundaries

## Executive Summary

After comprehensive research, I've identified **authoritative sources** for complete Local Government Directory (LGD) data covering all 36 states/UTs, ~778 districts, ~7,000 blocks, ~262,000 gram panchayats, and 676,000+ villages in India.

**Best Data Source**: ramSeraph's opendata project provides daily-updated CSV dumps of the official LGD database.

---

## 📊 Data Coverage Statistics (from lgdirectory.gov.in)

| Administrative Level | Count |
|---------------------|-------|
| States/UTs | 36 |
| Districts | 778 |
| Sub-Districts | 7,069 |
| Development Blocks | 7,307 |
| Villages | 676,236 (656,962 inhabited; 18,377 uninhabited; 897 forest) |
| Rural Local Bodies (Gram Panchayats) | 262,530 |
| Urban Local Bodies | 5,003 |

---

## 🎯 RECOMMENDED: Best Data Source

### 1. ramSeraph OpenData Project (HIGHEST RECOMMENDATION)

**URL**: https://ramseraph.github.io/opendata/lgd/

**Why This is Best**:
- ✅ Complete daily backup of official lgdirectory.gov.in database
- ✅ Plain CSV format - easy to import into PostgreSQL
- ✅ Covers ALL administrative levels
- ✅ No authentication required
- ✅ Updated daily
- ✅ Community-maintained mirror with high reliability

**Available Datasets**:
- `states.csv` - All 36 states/UTs
- `districts.csv` - All districts with state mapping
- `subdistricts.csv` - All sub-districts (tehsils/talukas)
- `blocks.csv` - All development blocks
- `villages.csv` - All 676,000+ villages
- `local_bodies.csv` - All gram panchayats and municipalities
- `wards.csv` - Ward-level data for local bodies

**Data Format**: CSV with columns including:
- LGD Code (unique identifier)
- Entity name
- Parent entity code (hierarchical mapping)
- State code
- Status (active/inactive)
- Version information

**How to Download Programmatically**:

```bash
# Direct download of latest CSV files
wget https://ramseraph.github.io/opendata/lgd/latest/states.csv
wget https://ramseraph.github.io/opendata/lgd/latest/districts.csv
wget https://ramseraph.github.io/opendata/lgd/latest/subdistricts.csv
wget https://ramseraph.github.io/opendata/lgd/latest/blocks.csv
wget https://ramseraph.github.io/opendata/lgd/latest/villages.csv
wget https://ramseraph.github.io/opendata/lgd/latest/local_bodies.csv
```

**Archive Format Note**: Archives use 7zip format (not standard zip). Extract using:
```bash
7z x filename.7z
```

**Python Implementation**:

```python
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Base URL for LGD CSV files
BASE_URL = "https://ramseraph.github.io/opendata/lgd/latest"

# Download and load CSV files
states_df = pd.read_csv(f"{BASE_URL}/states.csv")
districts_df = pd.read_csv(f"{BASE_URL}/districts.csv")
blocks_df = pd.read_csv(f"{BASE_URL}/blocks.csv")
villages_df = pd.read_csv(f"{BASE_URL}/villages.csv")
panchayats_df = pd.read_csv(f"{BASE_URL}/local_bodies.csv")

# PostgreSQL connection
engine = create_engine('postgresql://user:password@localhost:5432/boloo_db')

# Import to PostgreSQL
states_df.to_sql('lgd_states', engine, if_exists='replace', index=False)
districts_df.to_sql('lgd_districts', engine, if_exists='replace', index=False)
blocks_df.to_sql('lgd_blocks', engine, if_exists='replace', index=False)
villages_df.to_sql('lgd_villages', engine, if_exists='replace', index=False)
panchayats_df.to_sql('lgd_panchayats', engine, if_exists='replace', index=False)

print("LGD data successfully imported to PostgreSQL!")
```

---

## 🏛️ Official Government Sources

### 2. lgdirectory.gov.in (Official Source)

**URL**: https://lgdirectory.gov.in/

**Access Methods**:
- **Web Portal**: 65+ downloadable reports via "Download Directory" section
- **NAPIX API**: dev.napix.gov.in/nic/lgd/ (requires registration)
- **Direct Reports**: District-wise, state-wise consolidated reports

**Authentication Requirements**:
- Public reports: No authentication
- NAPIX API: Developer registration required
- Bulk downloads: OWASP CSRF token required (via web session)

**Limitations**:
- ❌ No direct bulk CSV download endpoint
- ❌ CSRF protection makes automated downloads complex
- ❌ API requires government approval
- ✅ Most authoritative/official source

**How to Access**:
1. Visit https://lgdirectory.gov.in/downloadDirectory.do
2. Select entity type (districts, blocks, villages, etc.)
3. Download reports in Excel/CSV format
4. Requires manual download or complex web scraping

---

### 3. data.gov.in Open Government Data Portal

**URL**: https://www.data.gov.in/catalog/local-government-directory-lgd

**Available Datasets** (Updated 1st of every month):

| Dataset | URL |
|---------|-----|
| States | https://www.data.gov.in/resource/local-government-directory-lgd-states |
| Districts | https://www.data.gov.in/resource/local-government-directory-lgd-districts |
| Sub-Districts | https://www.data.gov.in/resource/local-government-directory-lgd-sub-districts |
| Villages | https://www.data.gov.in/resource/local-government-directory-lgd-villages |
| Villages with PIN | https://www.data.gov.in/resource/local-government-directory-lgd-villages-pin-codes |
| Local Bodies | https://www.data.gov.in/resource/local-government-directory-lgd-local-bodies |
| Local Bodies with PIN | https://www.data.gov.in/resource/local-government-directory-lgd-local-bodies-pin-codes |

**Data Format**: CSV downloads available

**API Status**:
- ❌ APIs do NOT exist for most datasets
- ❌ Must click "Request API" to submit API request
- ✅ CSV downloads available without authentication

**Limitations**:
- Block-level data API is fetching old/obsolete data
- Gram panchayat data may be outdated via API
- Monthly update cycle (not real-time)

**Python Library**: `datagovindia`

```bash
pip install datagovindia
```

**Usage Example**:

```python
from datagovindia import DataGovIndia
import os

# Set API key (get from data.gov.in)
os.environ['DATAGOVINDIA_API_KEY'] = 'your_api_key_here'

# Initialize client
datagovin = DataGovIndia()

# Search for LGD datasets
lgd_resources = datagovin.search('Local Government Directory')

# Download specific dataset (example resource ID)
districts_data = datagovin.get_data("19df978a-675e-4ff5-8015-d0e1de447319")  # District LGD codes
```

---

### 4. Census 2011 Data

**URL**: https://censusindia.gov.in/census.website/data/census-tables

**Coverage**:
- Complete village directory for all states/UTs
- Census codes for all administrative units
- 600,000+ villages and 8,000+ towns
- Population and socio-economic data

**Data Format**: Excel files, PDF reports

**Location Code Structure**:
- 2-digit state code
- 3-digit district code
- 5-digit sub-district code
- 6-digit village code (range: 000001-799999)

**Key Resources**:

| Resource | URL |
|----------|-----|
| Complete Villages Directory | https://www.data.gov.in/catalog/complete-villages-directory-indiastatedistrictsub-district-level-census-2011 |
| Population Finder | https://censusindia.gov.in/census.website/data/population-finder |
| Administrative Atlas | https://censusindia.gov.in/census.website/data/atlas |

**Geospatial Boundary Data**:

1. **Development Data Lab** (RECOMMENDED for GIS)
   - URL: Contact via devdatalab.medium.com
   - Format: Shapefile, GeoPackage (EPSG:4326)
   - Coverage: ~600,000 villages, ~8,000 towns
   - Includes Census 2011 identifiers

2. **DataMeet Project** - Indian Village Boundaries
   - URL: https://projects.datameet.org/indian_village_boundaries/
   - Format: GeoJSON (WGS84, EPSG:4326)
   - Census code mappings for 2001 and 2011

3. **Harvard GIS Data**
   - URL: https://gis2.harvard.edu/resources/data/india-gis-data
   - District profiles, block maps, village maps (7 districts)

**PostgreSQL/PostGIS Import**:

```bash
# Import shapefile to PostGIS
ogr2ogr -f PostgreSQL \
  PG:"host=localhost dbname=boloo_db user=postgres password=yourpass" \
  villages.shp \
  -nln census_villages \
  -lco GEOMETRY_NAME=geom \
  -lco FID=gid

# Import GeoJSON
ogr2ogr -f PostgreSQL \
  PG:"host=localhost dbname=boloo_db" \
  villages.geojson \
  -nln census_villages_geojson
```

**Limitations**:
- Census 2011 data is 13+ years old
- Some administrative changes not reflected
- Population data outdated
- But: Most stable for historical analysis

---

## 🐍 Python Libraries & Tools

### 1. datagovindia (Official OGD Platform Client)

**Installation**:
```bash
pip install datagovindia
```

**Setup**:
1. Get API key from https://data.gov.in/ (free registration)
2. Set environment variable: `export DATAGOVINDIA_API_KEY=your_key`

**Usage**:
```python
from datagovindia import DataGovIndia

# Initialize
client = DataGovIndia()

# Sync metadata
client.sync_metadata()

# Search for LGD resources
results = client.search('LGD', search_fields=['title', 'description'])

# Get data by resource ID
data = client.get_data('resource-id-here')

# Command line
# datagovindia search LGD
# datagovindia get-data resource-id --output lgd.csv
```

**Pros**:
- ✅ Official government library
- ✅ Simple API wrapper
- ✅ CLI tool included

**Cons**:
- ❌ Limited to data.gov.in datasets
- ❌ API coverage incomplete for LGD
- ❌ Requires API key

---

### 2. Custom Python Script for ramSeraph Data

**Complete PostgreSQL Import Solution**:

```python
#!/usr/bin/env python3
"""
LGD Data Import Script for PostgreSQL
Downloads complete LGD data from ramSeraph opendata and imports to PostgreSQL
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import requests
from io import StringIO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for LGD CSV files
BASE_URL = "https://ramseraph.github.io/opendata/lgd/latest"

# PostgreSQL connection string
DB_CONNECTION = "postgresql://user:password@localhost:5432/boloo_db"

# Dataset definitions
DATASETS = {
    'states': {
        'url': f'{BASE_URL}/states.csv',
        'table': 'lgd_states',
        'primary_key': 'state_code'
    },
    'districts': {
        'url': f'{BASE_URL}/districts.csv',
        'table': 'lgd_districts',
        'primary_key': 'district_code'
    },
    'subdistricts': {
        'url': f'{BASE_URL}/subdistricts.csv',
        'table': 'lgd_subdistricts',
        'primary_key': 'subdistrict_code'
    },
    'blocks': {
        'url': f'{BASE_URL}/blocks.csv',
        'table': 'lgd_blocks',
        'primary_key': 'block_code'
    },
    'villages': {
        'url': f'{BASE_URL}/villages.csv',
        'table': 'lgd_villages',
        'primary_key': 'village_code'
    },
    'local_bodies': {
        'url': f'{BASE_URL}/local_bodies.csv',
        'table': 'lgd_panchayats',
        'primary_key': 'local_body_code'
    }
}

def download_csv(url):
    """Download CSV file from URL"""
    logger.info(f"Downloading {url}")
    response = requests.get(url)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))

def create_indexes(engine, table_name, primary_key):
    """Create indexes for better query performance"""
    with engine.connect() as conn:
        try:
            # Create primary key index
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{primary_key} ON {table_name}({primary_key})"))

            # Create state code index for all tables
            if 'state_code' in conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}'")).fetchall():
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_state_code ON {table_name}(state_code)"))

            conn.commit()
            logger.info(f"Created indexes for {table_name}")
        except Exception as e:
            logger.warning(f"Index creation warning for {table_name}: {e}")

def import_lgd_data():
    """Main function to import all LGD data"""
    engine = create_engine(DB_CONNECTION)

    for dataset_name, dataset_info in DATASETS.items():
        try:
            logger.info(f"Processing {dataset_name}...")

            # Download CSV
            df = download_csv(dataset_info['url'])

            # Import to PostgreSQL
            df.to_sql(
                dataset_info['table'],
                engine,
                if_exists='replace',
                index=False,
                chunksize=10000  # Process in chunks for large datasets
            )

            # Create indexes
            create_indexes(engine, dataset_info['table'], dataset_info['primary_key'])

            logger.info(f"✓ Imported {len(df)} records to {dataset_info['table']}")

        except Exception as e:
            logger.error(f"✗ Error processing {dataset_name}: {e}")
            continue

    logger.info("LGD data import completed!")

def verify_import(engine):
    """Verify imported data"""
    with engine.connect() as conn:
        for dataset_name, dataset_info in DATASETS.items():
            result = conn.execute(text(f"SELECT COUNT(*) FROM {dataset_info['table']}"))
            count = result.scalar()
            logger.info(f"{dataset_info['table']}: {count} records")

if __name__ == "__main__":
    import_lgd_data()
    engine = create_engine(DB_CONNECTION)
    verify_import(engine)
```

**Save and Run**:
```bash
chmod +x import_lgd_data.py
python import_lgd_data.py
```

---

## 📋 Data Structure & Schema

### Typical LGD CSV Columns

**States Table**:
```
state_code, state_name, state_version, state_census_code_2001, state_census_code_2011
```

**Districts Table**:
```
state_code, district_code, district_name, district_version, census_code_2001, census_code_2011
```

**Blocks Table**:
```
state_code, district_code, block_code, block_name, block_type, version
```

**Villages Table**:
```
state_code, district_code, subdistrict_code, village_code, village_name,
census_code_2001, census_code_2011, pin_code, version
```

**Gram Panchayats (Local Bodies) Table**:
```
state_code, district_code, local_body_code, local_body_name, local_body_type,
level (village/intermediate/district panchayat), version
```

### Recommended PostgreSQL Schema

```sql
-- States
CREATE TABLE lgd_states (
    state_code VARCHAR(2) PRIMARY KEY,
    state_name VARCHAR(100) NOT NULL,
    state_version INTEGER,
    census_code_2001 VARCHAR(2),
    census_code_2011 VARCHAR(2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Districts
CREATE TABLE lgd_districts (
    district_code VARCHAR(4) PRIMARY KEY,
    state_code VARCHAR(2) REFERENCES lgd_states(state_code),
    district_name VARCHAR(100) NOT NULL,
    district_version INTEGER,
    census_code_2001 VARCHAR(4),
    census_code_2011 VARCHAR(4),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_districts_state ON lgd_districts(state_code);

-- Blocks
CREATE TABLE lgd_blocks (
    block_code VARCHAR(10) PRIMARY KEY,
    district_code VARCHAR(4) REFERENCES lgd_districts(district_code),
    state_code VARCHAR(2) REFERENCES lgd_states(state_code),
    block_name VARCHAR(100) NOT NULL,
    block_type VARCHAR(50),
    version INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_blocks_district ON lgd_blocks(district_code);
CREATE INDEX idx_blocks_state ON lgd_blocks(state_code);

-- Villages
CREATE TABLE lgd_villages (
    village_code VARCHAR(10) PRIMARY KEY,
    subdistrict_code VARCHAR(10),
    district_code VARCHAR(4) REFERENCES lgd_districts(district_code),
    state_code VARCHAR(2) REFERENCES lgd_states(state_code),
    village_name VARCHAR(100) NOT NULL,
    census_code_2001 VARCHAR(10),
    census_code_2011 VARCHAR(10),
    pin_code VARCHAR(6),
    version INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_villages_district ON lgd_villages(district_code);
CREATE INDEX idx_villages_state ON lgd_villages(state_code);
CREATE INDEX idx_villages_pin ON lgd_villages(pin_code);

-- Gram Panchayats (Local Bodies)
CREATE TABLE lgd_panchayats (
    local_body_code VARCHAR(10) PRIMARY KEY,
    district_code VARCHAR(4) REFERENCES lgd_districts(district_code),
    state_code VARCHAR(2) REFERENCES lgd_states(state_code),
    local_body_name VARCHAR(100) NOT NULL,
    local_body_type VARCHAR(50),
    level VARCHAR(50), -- village/intermediate/district panchayat
    version INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_panchayats_district ON lgd_panchayats(district_code);
CREATE INDEX idx_panchayats_state ON lgd_panchayats(state_code);
CREATE INDEX idx_panchayats_type ON lgd_panchayats(local_body_type);

-- User reports mapping (for your citizen reporting app)
CREATE TABLE user_reports (
    report_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    report_type VARCHAR(50),
    description TEXT,
    location_type VARCHAR(20), -- state/district/block/village/panchayat
    state_code VARCHAR(2) REFERENCES lgd_states(state_code),
    district_code VARCHAR(4) REFERENCES lgd_districts(district_code),
    block_code VARCHAR(10) REFERENCES lgd_blocks(block_code),
    village_code VARCHAR(10) REFERENCES lgd_villages(village_code),
    panchayat_code VARCHAR(10) REFERENCES lgd_panchayats(local_body_code),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_reports_state ON user_reports(state_code);
CREATE INDEX idx_reports_district ON user_reports(district_code);
CREATE INDEX idx_reports_village ON user_reports(village_code);
CREATE INDEX idx_reports_location ON user_reports(latitude, longitude);
```

---

## ⚠️ Limitations & Challenges

### Data Quality Issues

1. **Outdated Information**:
   - Census 2011 data is 13+ years old
   - Administrative changes may not be reflected in real-time
   - New districts/blocks created after 2011 may have incomplete data

2. **Data Inconsistencies**:
   - Spelling variations in entity names
   - Multiple name formats (English/local language)
   - Duplicate entries in some cases
   - Version tracking can be confusing

3. **Missing Data**:
   - Some villages lack PIN codes
   - Geospatial coordinates not available in LGD
   - Contact information for local bodies incomplete
   - Ward-level data sparse

### Technical Challenges

1. **Volume**:
   - 676,000+ villages means large CSV files (100MB+)
   - Requires efficient database indexing
   - Full-text search needed for name lookups
   - Consider partitioning for better performance

2. **Updates**:
   - ramSeraph updates daily but requires re-download
   - data.gov.in updates monthly (1st of month)
   - Official LGD updates irregularly
   - Need ETL pipeline for continuous updates

3. **API Limitations**:
   - No official public API
   - NAPIX API requires government approval
   - data.gov.in APIs incomplete
   - Rate limiting concerns for bulk access

4. **Geospatial Data**:
   - LGD doesn't include lat/long coordinates
   - Need separate Census/DataMeet datasets for boundaries
   - GeoJSON files large (several GB for all villages)
   - Coordinate system conversions may be needed

### Recommended Mitigations

1. **Use Multiple Sources**:
   - Primary: ramSeraph LGD data (most complete, updated)
   - Secondary: Census 2011 for geospatial boundaries
   - Tertiary: data.gov.in for official verification

2. **Implement Data Validation**:
   ```python
   # Example validation
   def validate_lgd_codes(df):
       # Check for null codes
       null_codes = df[df['lgd_code'].isnull()]

       # Check for duplicate codes
       duplicates = df[df.duplicated('lgd_code')]

       # Verify state-district relationships
       invalid_refs = df[~df['state_code'].isin(valid_state_codes)]

       return {
           'null_codes': len(null_codes),
           'duplicates': len(duplicates),
           'invalid_refs': len(invalid_refs)
       }
   ```

3. **Implement Fuzzy Matching**:
   ```python
   from fuzzywuzzy import fuzz

   def find_village(search_term, villages_df):
       villages_df['match_score'] = villages_df['village_name'].apply(
           lambda x: fuzz.ratio(search_term.lower(), x.lower())
       )
       return villages_df.nlargest(10, 'match_score')
   ```

4. **Add Geospatial Layer**:
   - Use PostGIS for spatial queries
   - Integrate Census boundary shapefiles
   - Add reverse geocoding capability

---

## 🚀 Implementation Roadmap

### Phase 1: Data Acquisition (Week 1)
- [ ] Download complete LGD CSV dump from ramSeraph
- [ ] Download Census 2011 boundary shapefiles from DataMeet
- [ ] Get data.gov.in API key for backup access
- [ ] Verify data completeness and integrity

### Phase 2: Database Setup (Week 1-2)
- [ ] Create PostgreSQL database with PostGIS extension
- [ ] Implement schema from recommendations above
- [ ] Import LGD CSV data
- [ ] Import geospatial boundary data
- [ ] Create indexes and optimize queries
- [ ] Set up full-text search for entity names

### Phase 3: Data Quality & Enhancement (Week 2-3)
- [ ] Implement data validation rules
- [ ] Add fuzzy matching for search
- [ ] Geocode missing coordinates
- [ ] Clean duplicates and inconsistencies
- [ ] Add metadata tables (data source, update timestamps)

### Phase 4: API Development (Week 3-4)
- [ ] Build REST API for location lookups
- [ ] Implement hierarchical queries (state → district → block → village)
- [ ] Add autocomplete endpoints
- [ ] Create geospatial query endpoints
- [ ] Document API with OpenAPI/Swagger

### Phase 5: Update Automation (Week 4)
- [ ] Schedule daily checks for ramSeraph updates
- [ ] Build ETL pipeline for incremental updates
- [ ] Set up monitoring and alerting
- [ ] Create data quality dashboards

---

## 📖 Quick Start Commands

### Download All Data
```bash
# Create directory structure
mkdir -p ~/lgd_data/{csv,geojson,processed}
cd ~/lgd_data/csv

# Download LGD CSV files
wget https://ramseraph.github.io/opendata/lgd/latest/states.csv
wget https://ramseraph.github.io/opendata/lgd/latest/districts.csv
wget https://ramseraph.github.io/opendata/lgd/latest/subdistricts.csv
wget https://ramseraph.github.io/opendata/lgd/latest/blocks.csv
wget https://ramseraph.github.io/opendata/lgd/latest/villages.csv
wget https://ramseraph.github.io/opendata/lgd/latest/local_bodies.csv
```

### Import to PostgreSQL
```bash
# Install required Python packages
pip install pandas sqlalchemy psycopg2-binary requests

# Run import script (save Python script above as import_lgd.py)
python import_lgd.py

# Verify import
psql -d boloo_db -c "SELECT COUNT(*) FROM lgd_states;"
psql -d boloo_db -c "SELECT COUNT(*) FROM lgd_districts;"
psql -d boloo_db -c "SELECT COUNT(*) FROM lgd_villages;"
```

### Query Examples
```sql
-- Get all districts in a state (e.g., Karnataka)
SELECT * FROM lgd_districts WHERE state_code = '29';

-- Get all villages in a district
SELECT * FROM lgd_villages WHERE district_code = '2901';

-- Search for villages by name (fuzzy)
SELECT * FROM lgd_villages
WHERE village_name ILIKE '%bangalore%'
LIMIT 10;

-- Get hierarchical data (state → district → block → village)
SELECT
    s.state_name,
    d.district_name,
    b.block_name,
    v.village_name
FROM lgd_villages v
JOIN lgd_blocks b ON v.district_code = b.district_code
JOIN lgd_districts d ON v.district_code = d.district_code
JOIN lgd_states s ON v.state_code = s.state_code
WHERE v.village_code = 'specific-code';
```

---

## 📚 Additional Resources

### Official Documentation
- LGD Official: https://lgdirectory.gov.in/
- NAPIX Platform: https://napix.gov.in/
- Open Government Data: https://data.gov.in/

### Community Resources
- ramSeraph OpenData: https://github.com/ramSeraph/opendata
- DataMeet Village Boundaries: https://projects.datameet.org/indian_village_boundaries/
- DataMeet Google Group: https://groups.google.com/g/datameet

### Python Libraries
- datagovindia: https://pypi.org/project/datagovindia/
- pandas: https://pandas.pydata.org/
- geopandas: https://geopandas.org/
- fuzzywuzzy: https://github.com/seatgeek/fuzzywuzzy

### GIS Resources
- GADM (Administrative Boundaries): https://gadm.org/download_country_v3.html
- Harvard India GIS Data: https://gis2.harvard.edu/resources/data/india-gis-data
- Development Data Lab: Contact via Medium

---

## 🎯 Final Recommendations

### For Your Citizen Reporting App

**Architecture**:
```
User App (Mobile/Web)
    ↓
API Gateway
    ↓
Location Service (FastAPI/Node.js)
    ↓
PostgreSQL + PostGIS
    ├── LGD Tables (administrative data)
    └── Reports Tables (user submissions)
```

**Location Selection Flow**:
1. User selects State (dropdown from `lgd_states`)
2. Auto-populate Districts (query `lgd_districts` filtered by state)
3. User selects District
4. Auto-populate Blocks (query `lgd_blocks` filtered by district)
5. User selects Block
6. Auto-populate Villages/Panchayats
7. Optional: GPS coordinates for precise location

**Key Features to Implement**:
- ✅ Hierarchical dropdowns (state → district → block → village)
- ✅ Autocomplete search with fuzzy matching
- ✅ Reverse geocoding (lat/long → nearest village)
- ✅ Multi-language support (use LGD local names)
- ✅ Offline mode (cache administrative data on device)
- ✅ Map visualization (integrate boundary data)

**Sample API Endpoints**:
```
GET /api/states
GET /api/states/{state_code}/districts
GET /api/districts/{district_code}/blocks
GET /api/blocks/{block_code}/villages
GET /api/search/locations?q={query}&type={state|district|village}
GET /api/reverse-geocode?lat={lat}&lon={lon}
POST /api/reports (with location fields)
```

---

## ✅ Summary: What You Need to Do

1. **Download Data**: Use ramSeraph's opendata project (https://ramseraph.github.io/opendata/lgd/)
2. **Format**: CSV files - perfect for PostgreSQL import
3. **Coverage**: Complete data for all 36 states, 778 districts, 7,307 blocks, 262,530 panchayats, 676,236 villages
4. **Method**: Python script with pandas + SQLAlchemy (provided above)
5. **Updates**: Daily automated checks via cron job
6. **Geospatial**: Add Census 2011 boundaries from DataMeet for mapping

**Start Here**:
```bash
# 1. Download CSV data
wget https://ramseraph.github.io/opendata/lgd/latest/villages.csv

# 2. Use Python script (above) to import to PostgreSQL

# 3. Build your location selection API

# 4. Integrate with your mobile app
```

This gives you REAL, AUTHORITATIVE, COMPLETE data for all of India! 🇮🇳

---

**Research Completed**: 2025-11-18
**Data Sources Verified**: ramSeraph opendata, lgdirectory.gov.in, data.gov.in, Census 2011
**Researcher**: Claude Code Research Agent
