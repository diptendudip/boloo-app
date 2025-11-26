# LGD (Local Government Directory) Integration Plan

## Overview

The LGD (Local Government Directory) maintains authoritative data for all Indian administrative boundaries at https://lgdirectory.gov.in. Integrating this data will improve location validation accuracy by cross-referencing against official government records.

## Current Location System

### Strengths
- ✅ GPS boundary detection working (Mappls + Nominatim)
- ✅ Hindi and English address validation
- ✅ Hierarchical location storage (street → village → panchayat → block → district → state)
- ✅ Confidence scoring for results
- ✅ Free-tier geocoding (no API costs)

### Gaps
- ❌ No validation against authoritative government data
- ❌ Spelling variations not normalized (e.g., "Bastar" vs "Baster")
- ❌ No LGD codes stored for administrative boundaries
- ❌ Cannot verify if a village actually belongs to reported panchayat/block
- ❌ No offline fallback for location validation

## LGD Data Structure

### What LGD Provides
- **LGD Codes**: Unique identifiers for every administrative unit
- **Hierarchies**: Complete parent-child relationships
  - State → District → Sub-Division → Block → Panchayat → Village
- **Name Variations**: Official names in multiple languages
- **Census Data**: Integration with Census 2011 codes
- **GIS Boundaries**: Geographic boundary data (for some levels)

### Example LGD Hierarchy
```
Chhattisgarh (State)
  └─ Bastar (District)
      └─ Lohandiguda (Block)
          └─ Madar (Gram Panchayat)
              └─ Madar (Village)
```

### LGD API/Data Access
LGD provides data through:
1. **Public Website**: https://lgdirectory.gov.in/
   - Browse hierarchies
   - Download Excel/CSV exports
2. **Open Data Portal**: https://data.gov.in/
   - Bulk downloads of LGD datasets
   - Updated quarterly
3. **Web Scraping**: (as fallback)
   - Parse HTML pages programmatically
   - Extract LGD codes and hierarchies

## Integration Architecture

### Phase 1: Data Acquisition & Storage

#### 1.1 Database Schema Extensions
```sql
-- LGD administrative units table
CREATE TABLE lgd_admin_units (
    id SERIAL PRIMARY KEY,
    lgd_code VARCHAR(20) UNIQUE NOT NULL,
    name_en VARCHAR(255) NOT NULL,
    name_hi VARCHAR(255),
    name_local VARCHAR(255),
    level VARCHAR(20) NOT NULL, -- state, district, block, panchayat, village
    parent_lgd_code VARCHAR(20),
    state_code VARCHAR(5),
    district_code VARCHAR(5),
    census_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (parent_lgd_code) REFERENCES lgd_admin_units(lgd_code)
);

CREATE INDEX idx_lgd_name_en ON lgd_admin_units(name_en);
CREATE INDEX idx_lgd_name_hi ON lgd_admin_units(name_hi);
CREATE INDEX idx_lgd_level ON lgd_admin_units(level);
CREATE INDEX idx_lgd_parent ON lgd_admin_units(parent_lgd_code);

-- Name variations/aliases table (for fuzzy matching)
CREATE TABLE lgd_name_aliases (
    id SERIAL PRIMARY KEY,
    lgd_code VARCHAR(20) NOT NULL,
    alias VARCHAR(255) NOT NULL,
    language VARCHAR(10), -- en, hi, local
    source VARCHAR(50), -- lgd, census, osm, user_report
    confidence FLOAT DEFAULT 1.0,

    FOREIGN KEY (lgd_code) REFERENCES lgd_admin_units(lgd_code)
);

CREATE INDEX idx_alias_name ON lgd_name_aliases(alias);

-- Add LGD codes to existing tables
ALTER TABLE users ADD COLUMN location_village_lgd_code VARCHAR(20);
ALTER TABLE users ADD COLUMN location_panchayat_lgd_code VARCHAR(20);
ALTER TABLE users ADD COLUMN location_block_lgd_code VARCHAR(20);
ALTER TABLE users ADD COLUMN location_district_lgd_code VARCHAR(20);
ALTER TABLE users ADD COLUMN location_state_lgd_code VARCHAR(20);

ALTER TABLE cases ADD COLUMN location_village_lgd_code VARCHAR(20);
ALTER TABLE cases ADD COLUMN location_block_lgd_code VARCHAR(20);
ALTER TABLE cases ADD COLUMN location_district_lgd_code VARCHAR(20);
```

#### 1.2 Data Scraper/Importer
```python
# backend/app/services/lgd_importer.py

class LGDDataImporter:
    """
    Import LGD data from government sources
    """

    def download_bulk_data(self, state: str = "Chhattisgarh"):
        """
        Download LGD bulk data from data.gov.in
        - State, District, Block, Panchayat, Village datasets
        """
        pass

    def parse_excel_data(self, file_path: str):
        """
        Parse downloaded Excel/CSV files
        """
        pass

    def scrape_lgd_website(self, state_code: str):
        """
        Fallback: Scrape data from lgdirectory.gov.in
        """
        pass

    def import_to_database(self, data: list):
        """
        Insert parsed data into lgd_admin_units table
        """
        pass

    def build_name_aliases(self):
        """
        Generate alias variations for fuzzy matching
        - Handle Hindi transliteration variants
        - Common misspellings
        - Short names (e.g., "CG" for "Chhattisgarh")
        """
        pass
```

### Phase 2: Location Validation Service

#### 2.1 Enhanced Validator
```python
# backend/app/services/lgd_location_validator.py

class LGDLocationValidator:
    """
    Validate locations against LGD authoritative data
    """

    def validate_hierarchy(
        self,
        village: str,
        panchayat: str = None,
        block: str = None,
        district: str = None,
        state: str = "Chhattisgarh"
    ) -> Dict[str, Any]:
        """
        Validate that village → panchayat → block → district hierarchy is correct

        Returns:
        {
            "is_valid": True/False,
            "lgd_codes": {
                "state": "22",
                "district": "398",
                "block": "3151",
                "panchayat": "123456",
                "village": "234567"
            },
            "standardized_names": {
                "village": "मादर",
                "panchayat": "मादर ग्राम पंचायत",
                "block": "लोहंडीगुड़ा",
                "district": "बस्तर",
                "state": "छत्तीसगढ़"
            },
            "confidence": 0.95,
            "issues": []  # e.g., ["Panchayat name mismatch"]
        }
        """
        pass

    def fuzzy_match_location(self, name: str, level: str, parent_lgd_code: str = None):
        """
        Fuzzy match user input to LGD records
        - Handle spelling variations
        - Hindi/English transliteration
        - Phonetic matching
        """
        pass

    def suggest_corrections(self, name: str, level: str):
        """
        Suggest correct names when user input doesn't match
        """
        pass

    def enrich_with_lgd_data(self, location: Dict) -> Dict:
        """
        Take user-provided location, add LGD codes and official names
        """
        pass
```

#### 2.2 Integration with Existing Services
```python
# backend/app/services/location_validator.py (Enhanced)

class HybridLocationValidator:
    """
    Now combines: Geocoding APIs + LGD Validation
    """

    def validate_and_enrich_location(
        self,
        location_text: str,
        lat: float = None,
        lng: float = None,
        district_hint: str = None,
        state_hint: str = "Chhattisgarh"
    ) -> Dict[str, Any]:
        """
        Enhanced validation flow:
        1. Geocode using Mappls/Nominatim (get lat/lng + initial hierarchy)
        2. Validate against LGD data (verify hierarchy + add LGD codes)
        3. Return combined result with confidence score
        """

        # Step 1: Geocode
        geocoded = self.geocode_location(location_text, district_hint, state_hint)

        # Step 2: Validate with LGD
        lgd_validator = LGDLocationValidator()
        lgd_validated = lgd_validator.validate_hierarchy(
            village=geocoded.get("village"),
            panchayat=geocoded.get("panchayat"),
            block=geocoded.get("block"),
            district=geocoded.get("district"),
            state=geocoded.get("state")
        )

        # Step 3: Combine results
        return {
            "is_valid": geocoded["is_valid"] and lgd_validated["is_valid"],
            "lat": geocoded.get("lat"),
            "lng": geocoded.get("lng"),
            "admin_hierarchy": lgd_validated["standardized_names"],
            "lgd_codes": lgd_validated["lgd_codes"],
            "confidence": (geocoded["confidence"] + lgd_validated["confidence"]) / 2,
            "formatted_address": self.format_address(lgd_validated["standardized_names"]),
            "sources": {
                "geocoding": geocoded["source"],  # mappls/nominatim
                "validation": "lgd"
            }
        }
```

### Phase 3: API Endpoints

#### 3.1 New Endpoints
```python
# backend/app/routers/location.py (additions)

@router.get("/api/location/lgd/search")
async def search_lgd(
    query: str,
    level: str,  # village, panchayat, block, district
    parent_lgd_code: str = None,
    limit: int = 10
):
    """
    Search LGD database
    - Autocomplete for location names
    - Filter by administrative level
    - Restrict to children of parent unit
    """
    pass

@router.get("/api/location/lgd/hierarchy/{lgd_code}")
async def get_lgd_hierarchy(lgd_code: str):
    """
    Get full hierarchy for an LGD code
    Returns: State → District → Block → Panchayat → Village
    """
    pass

@router.post("/api/location/lgd/validate")
async def validate_with_lgd(location: LocationCapture):
    """
    Validate location specifically against LGD data
    (separate from GPS/geocoding validation)
    """
    pass
```

### Phase 4: Smart Chat Integration

#### 4.1 Location Confirmation Enhancement
```python
# When user confirms profile location in chat:

# BEFORE (current):
location = {
    "village": "मादर",
    "block": "लोहंडीगुड़ा",
    "district": "बस्तर"
}

# AFTER (with LGD):
location = {
    "village": "मादर",
    "village_lgd_code": "234567",
    "panchayat": "मादर ग्राम पंचायत",
    "panchayat_lgd_code": "123456",
    "block": "लोहंडीगुड़ा",
    "block_lgd_code": "3151",
    "district": "बस्तर",
    "district_lgd_code": "398",
    "state": "छत्तीसगढ़",
    "state_lgd_code": "22",
    "validated_by_lgd": True,
    "lgd_confidence": 0.98
}
```

#### 4.2 Street-Level Override
```python
# User says: "Same village but different street"

# System validates:
- Village LGD code matches? ✓
- Panchayat LGD code matches? ✓
- Block LGD code matches? ✓
- Only street name changed? ✓

# Allow override ✅
```

## Implementation Tasks

### Task 1: Data Acquisition (Priority: HIGH)
- [ ] Download LGD bulk datasets for Chhattisgarh from data.gov.in
- [ ] Create database schema (migrations for lgd_admin_units, lgd_name_aliases)
- [ ] Write data parser (Excel/CSV to database)
- [ ] Import Chhattisgarh data (districts, blocks, panchayats, villages)
- [ ] Build name alias table for fuzzy matching

### Task 2: Validation Service (Priority: HIGH)
- [ ] Implement LGDLocationValidator class
- [ ] Add fuzzy matching algorithm (phonetic + edit distance)
- [ ] Create hierarchy validation logic
- [ ] Integrate with existing HybridLocationValidator
- [ ] Add confidence scoring

### Task 3: API Endpoints (Priority: MEDIUM)
- [ ] Create /lgd/search endpoint for autocomplete
- [ ] Create /lgd/hierarchy endpoint
- [ ] Create /lgd/validate endpoint
- [ ] Update existing location endpoints to include LGD data
- [ ] Add API documentation

### Task 4: Database Migration (Priority: HIGH)
- [ ] Add LGD code columns to users table
- [ ] Add LGD code columns to cases table
- [ ] Backfill LGD codes for existing data (if possible)
- [ ] Create indexes for performance

### Task 5: Mobile App Updates (Priority: MEDIUM)
- [ ] Update TypeScript interfaces with LGD fields
- [ ] Show LGD validation status in UI
- [ ] Add LGD code display in profile
- [ ] Autocomplete suggestions from LGD data

### Task 6: Smart Chat Integration (Priority: LOW)
- [ ] Modify chat to include LGD codes in location confirmation
- [ ] Validate street-level overrides against LGD hierarchy
- [ ] Show official names from LGD in chat responses

### Task 7: Testing & Documentation (Priority: MEDIUM)
- [ ] Test with real Chhattisgarh locations
- [ ] Test fuzzy matching with common misspellings
- [ ] Test Hindi/English variations
- [ ] Document LGD integration in API docs
- [ ] Create admin guide for LGD data updates

## Data Sources

### Primary
- **LGD Portal**: https://lgdirectory.gov.in/
- **Open Government Data**: https://data.gov.in/
- **Download URLs**:
  - States: https://lgdirectory.gov.in/globalStateList.do
  - Districts: https://lgdirectory.gov.in/stateWiseDistrict.do
  - Blocks: https://lgdirectory.gov.in/districtWiseBlock.do
  - Villages: https://lgdirectory.gov.in/blockWiseVillage.do

### Secondary (for verification)
- Census 2011 data
- OpenStreetMap admin boundaries
- State government portals

## Success Metrics

### Accuracy Improvements
- **Current**: ~70-85% accuracy (Mappls/Nominatim only)
- **Target**: 95%+ accuracy with LGD validation

### Coverage
- **Phase 1**: Complete coverage of Chhattisgarh
- **Phase 2**: Expand to all tribal states
- **Phase 3**: All-India coverage

### Performance
- LGD validation should add < 100ms latency
- Fuzzy matching for 10K villages: < 200ms
- Database queries should use indexes effectively

## Challenges & Mitigation

### Challenge 1: Data Freshness
- **Problem**: LGD data updated quarterly, changes may lag
- **Solution**:
  - Schedule automatic quarterly imports
  - Allow manual admin updates
  - Show "last updated" timestamp

### Challenge 2: Spelling Variations
- **Problem**: Users spell village names inconsistently
- **Solution**:
  - Build comprehensive alias table
  - Use phonetic matching (Soundex, Metaphone)
  - Learn from user corrections

### Challenge 3: Missing Data
- **Problem**: Not all villages have GPS coordinates in LGD
- **Solution**:
  - Fall back to geocoding APIs
  - Use centroid of parent block
  - Allow user to provide GPS

### Challenge 4: Multilingual Complexity
- **Problem**: Hindi, English, and local language variations
- **Solution**:
  - Store all name variants
  - Transliteration libraries
  - Allow user to select preferred language

## Timeline Estimate

- **Week 1-2**: Data acquisition + database schema + import script
- **Week 3**: LGD validation service implementation
- **Week 4**: API endpoints + testing
- **Week 5**: Mobile app integration
- **Week 6**: Smart chat integration + documentation

**Total**: ~6 weeks for full implementation

## Next Immediate Steps

1. ✅ Create this plan document
2. ⏭️ Download Chhattisgarh LGD data from data.gov.in
3. ⏭️ Create database migrations for LGD tables
4. ⏭️ Write data import script
5. ⏭️ Import data and verify in database
