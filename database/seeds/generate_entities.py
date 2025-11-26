"""
Generate seed data for government entities (Districts, Blocks, GPs, Departments)
with proper escalation hierarchy and coverage areas.
"""

import json
import uuid
from typing import List, Dict
import random

# Chhattisgarh district names (28 districts as of 2024)
DISTRICTS = [
    "Raipur", "Bilaspur", "Durg", "Korba", "Rajnandgaon",
    "Raigarh", "Bastar", "Surguja", "Jashpur", "Koriya",
    "Dhamtari", "Mahasamund", "Kanker", "Kabirdham", "Balod",
    "Baloda Bazar", "Bemetara", "Gariaband", "Janjgir-Champa", "Kondagaon",
    "Mungeli", "Narayanpur", "Sukma", "Surajpur", "Balrampur",
    "Gaurela-Pendra-Marwahi", "Mohla-Manpur", "Sarangarh-Bilaigarh", "Manendragarh", "Sakti"
]

# Sample Block names (common in rural India)
BLOCK_SUFFIXES = [
    "Block", "Panchayat Samiti", "Development Block", "Mandal"
]

BLOCK_NAMES = [
    "Central", "North", "South", "East", "West",
    "Sadar", "Urban", "Rural", "Main", "Upper"
]

# Sample GP (Gram Panchayat) names
GP_NAMES = [
    "Barhi", "Lapung", "Mandar", "Sisai", "Torpa",
    "Netarhat", "Bero", "Tandwa", "Mahuadanr", "Chandwa",
    "Ramgarh", "Gola", "Itki", "Ormanjhi", "Kanke",
    "Ratu", "Namkum", "Bundu", "Tamar", "Silli",
    "Angara", "Barkatha", "Barwadih", "Chandankiyari", "Chatra",
    "Hunterganj", "Itkhori", "Lawalong", "Mayurhand", "Pathalgada"
]

# Department names
DEPARTMENTS = [
    "District Electricity Department",
    "Public Health Engineering Department",
    "Rural Development Department",
    "Social Welfare Department",
    "Agriculture Department",
    "District Health Department",
    "District Education Department",
    "District Police Department",
    "Revenue Department",
    "Forest Department"
]


def generate_coverage_geojson(lat: float, lng: float, radius_km: float = 20) -> Dict:
    """
    Generate a simple bounding box GeoJSON for coverage area.
    In production, this would be actual administrative boundaries.
    """
    # Approximate: 1 degree lat ~111 km, 1 degree lng ~111*cos(lat) km
    lat_offset = radius_km / 111.0
    lng_offset = radius_km / (111.0 * 0.85)  # Approximation for India's latitude

    return {
        "type": "Polygon",
        "coordinates": [[
            [lng - lng_offset, lat - lat_offset],
            [lng + lng_offset, lat - lat_offset],
            [lng + lng_offset, lat + lat_offset],
            [lng - lng_offset, lat + lat_offset],
            [lng - lng_offset, lat - lat_offset]
        ]]
    }


def generate_entities() -> List[Dict]:
    """Generate 100+ entities with proper hierarchy."""
    entities = []

    # Generate State-level entities (root of escalation)
    state_id = str(uuid.uuid4())
    state_lat, state_lng = 21.2787, 81.8661  # Chhattisgarh approximate center (Raipur)

    entities.append({
        "id": state_id,
        "name": "Chhattisgarh State Administration",
        "type": "district",  # Using district type for state-level
        "contact_phone": "+91-771-2221800",
        "contact_email": "cm.office@cg.gov.in",
        "escalation_parent_id": None,  # Root
        "coverage_geojson": json.dumps(generate_coverage_geojson(state_lat, state_lng, 200)),
        "metadata": json.dumps({"level": "state", "code": "CG"}),
        "is_active": True
    })

    # Generate 30 Districts
    district_ids = []
    for i, district_name in enumerate(DISTRICTS[:30]):
        district_id = str(uuid.uuid4())
        district_ids.append({
            "id": district_id,
            "name": district_name,
            "index": i
        })

        # Vary location slightly for each district
        lat = state_lat + (i % 6 - 3) * 0.5
        lng = state_lng + (i // 6 - 2) * 0.5

        entities.append({
            "id": district_id,
            "name": f"{district_name} District",
            "type": "district",
            "contact_phone": f"+91-9{random.randint(100000000, 999999999)}",
            "contact_email": f"dc.{district_name.lower().replace(' ', '').replace('-', '')}@cg.gov.in",
            "escalation_parent_id": state_id,
            "coverage_geojson": json.dumps(generate_coverage_geojson(lat, lng, 50)),
            "metadata": json.dumps({"level": "district", "code": f"CG-{i+1:02d}"}),
            "is_active": True
        })

    # Generate 60 Blocks (2 per district)
    block_ids = []
    for i, district in enumerate(district_ids[:30]):
        for j in range(2):
            block_id = str(uuid.uuid4())
            block_name = f"{random.choice(BLOCK_NAMES)} {random.choice(BLOCK_SUFFIXES)}"
            block_ids.append({
                "id": block_id,
                "name": block_name,
                "district_id": district["id"],
                "index": i * 2 + j
            })

            lat = state_lat + (district["index"] % 6 - 3) * 0.5 + j * 0.2
            lng = state_lng + (district["index"] // 6 - 2) * 0.5 + j * 0.2

            entities.append({
                "id": block_id,
                "name": f"{block_name}, {district['name']}",
                "type": "block",
                "contact_phone": f"+91-9{random.randint(100000000, 999999999)}",
                "contact_email": f"bdo.{block_name.lower().replace(' ', '').replace('-', '')}.{district['name'].lower().replace(' ', '').replace('-', '')}@cg.gov.in",
                "escalation_parent_id": district["id"],
                "coverage_geojson": json.dumps(generate_coverage_geojson(lat, lng, 20)),
                "metadata": json.dumps({"level": "block", "district": district["name"]}),
                "is_active": True
            })

    # Generate 100 GPs (Gram Panchayats) - ~1-2 per block
    for i, gp_name in enumerate(GP_NAMES[:100]):
        gp_id = str(uuid.uuid4())
        block = random.choice(block_ids)

        # Find the district for this block
        district_name = block["name"].split(",")[-1].strip()

        lat = state_lat + (i % 10 - 5) * 0.1
        lng = state_lng + (i // 10 - 5) * 0.1

        entities.append({
            "id": gp_id,
            "name": f"{gp_name} Gram Panchayat",
            "type": "gp",
            "contact_phone": f"+91-9{random.randint(100000000, 999999999)}",
            "contact_email": f"gp.{gp_name.lower()}@cg.gov.in",
            "escalation_parent_id": block["id"],
            "coverage_geojson": json.dumps(generate_coverage_geojson(lat, lng, 5)),
            "metadata": json.dumps({"level": "gp", "block": block["name"], "villages": random.randint(3, 10)}),
            "is_active": True
        })

    # Generate 10 Departments (state-level, escalate to state)
    for i, dept_name in enumerate(DEPARTMENTS):
        dept_id = str(uuid.uuid4())

        entities.append({
            "id": dept_id,
            "name": dept_name,
            "type": "dept",
            "contact_phone": f"+91-771-2{random.randint(100000, 999999)}",
            "contact_email": f"{dept_name.lower().replace(' ', '.').replace('department', 'dept')}@cg.gov.in",
            "escalation_parent_id": state_id,
            "coverage_geojson": json.dumps(generate_coverage_geojson(state_lat, state_lng, 200)),
            "metadata": json.dumps({"level": "department", "scope": "state-wide"}),
            "is_active": True
        })

    return entities


def generate_sql(entities: List[Dict]) -> str:
    """Generate SQL INSERT statements."""
    sql = "-- Generated Entity Seed Data\n\n"

    for entity in entities:
        sql += f"""INSERT INTO entities (id, name, type, contact_phone, contact_email, escalation_parent_id, coverage_geojson, metadata, is_active) VALUES (
    '{entity['id']}',
    '{entity['name']}',
    '{entity['type']}',
    '{entity['contact_phone']}',
    '{entity['contact_email']}',
    {'NULL' if entity['escalation_parent_id'] is None else f"'{entity['escalation_parent_id']}'"},
    '{entity['coverage_geojson']}',
    '{entity['metadata']}',
    {entity['is_active']}
);\n\n"""

    sql += "COMMIT;\n"
    return sql


def generate_csv(entities: List[Dict]) -> str:
    """Generate CSV for bulk import."""
    csv = "id,name,type,contact_phone,contact_email,escalation_parent_id,coverage_geojson,metadata,is_active\n"

    for entity in entities:
        parent_id = entity['escalation_parent_id'] if entity['escalation_parent_id'] else ''
        csv += f'"{entity["id"]}","{entity["name"]}","{entity["type"]}","{entity["contact_phone"]}","{entity["contact_email"]}","{parent_id}",\'{entity["coverage_geojson"]}\',\'{entity["metadata"]}\',{entity["is_active"]}\n'

    return csv


if __name__ == "__main__":
    print("Generating entity seed data...")
    entities = generate_entities()
    print(f"Generated {len(entities)} entities")

    # Generate SQL file
    sql_content = generate_sql(entities)
    with open("02_entities.sql", "w") as f:
        f.write(sql_content)
    print("✓ Generated 02_entities.sql")

    # Generate CSV file
    csv_content = generate_csv(entities)
    with open("entities_template.csv", "w") as f:
        f.write(csv_content)
    print("✓ Generated entities_template.csv")

    print("\nEntity breakdown:")
    print(f"  State: 1")
    print(f"  Districts: 30")
    print(f"  Blocks: 60")
    print(f"  Gram Panchayats: 100")
    print(f"  Departments: 10")
    print(f"  Total: {len(entities)}")
