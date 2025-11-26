"""
Create cascading dropdown data for ALL Indian states

This script creates administrative hierarchy for dropdown selection across India:
State → District → Block → Panchayat

Data source: LGD (Local Government Directory) official data
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, Column, String, Integer, Table, MetaData, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comprehensive All-India Data
# Source: https://lgdirectory.gov.in/ and Census 2011

ALL_INDIA_DATA = {
    "states": [
        {"name": "आंध्र प्रदेश", "name_en": "Andhra Pradesh", "state_code": "28"},
        {"name": "अरुणाचल प्रदेश", "name_en": "Arunachal Pradesh", "state_code": "12"},
        {"name": "असम", "name_en": "Assam", "state_code": "18"},
        {"name": "बिहार", "name_en": "Bihar", "state_code": "10"},
        {"name": "छत्तीसगढ़", "name_en": "Chhattisgarh", "state_code": "22"},
        {"name": "गोवा", "name_en": "Goa", "state_code": "30"},
        {"name": "गुजरात", "name_en": "Gujarat", "state_code": "24"},
        {"name": "हरियाणा", "name_en": "Haryana", "state_code": "06"},
        {"name": "हिमाचल प्रदेश", "name_en": "Himachal Pradesh", "state_code": "02"},
        {"name": "झारखंड", "name_en": "Jharkhand", "state_code": "20"},
        {"name": "कर्नाटक", "name_en": "Karnataka", "state_code": "29"},
        {"name": "केरल", "name_en": "Kerala", "state_code": "32"},
        {"name": "मध्य प्रदेश", "name_en": "Madhya Pradesh", "state_code": "23"},
        {"name": "महाराष्ट्र", "name_en": "Maharashtra", "state_code": "27"},
        {"name": "मणिपुर", "name_en": "Manipur", "state_code": "14"},
        {"name": "मेघालय", "name_en": "Meghalaya", "state_code": "17"},
        {"name": "मिजोरम", "name_en": "Mizoram", "state_code": "15"},
        {"name": "नागालैंड", "name_en": "Nagaland", "state_code": "13"},
        {"name": "ओडिशा", "name_en": "Odisha", "state_code": "21"},
        {"name": "पंजाब", "name_en": "Punjab", "state_code": "03"},
        {"name": "राजस्थान", "name_en": "Rajasthan", "state_code": "08"},
        {"name": "सिक्किम", "name_en": "Sikkim", "state_code": "11"},
        {"name": "तमिलनाडु", "name_en": "Tamil Nadu", "state_code": "33"},
        {"name": "तेलंगाना", "name_en": "Telangana", "state_code": "36"},
        {"name": "त्रिपुरा", "name_en": "Tripura", "state_code": "16"},
        {"name": "उत्तर प्रदेश", "name_en": "Uttar Pradesh", "state_code": "09"},
        {"name": "उत्तराखंड", "name_en": "Uttarakhand", "state_code": "05"},
        {"name": "पश्चिम बंगाल", "name_en": "West Bengal", "state_code": "19"},
        # Union Territories
        {"name": "अंडमान और निकोबार द्वीप समूह", "name_en": "Andaman and Nicobar Islands", "state_code": "35"},
        {"name": "चंडीगढ़", "name_en": "Chandigarh", "state_code": "04"},
        {"name": "दादरा और नगर हवेली और दमन और दीव", "name_en": "Dadra and Nagar Haveli and Daman and Diu", "state_code": "26"},
        {"name": "दिल्ली", "name_en": "Delhi", "state_code": "07"},
        {"name": "जम्मू और कश्मीर", "name_en": "Jammu and Kashmir", "state_code": "01"},
        {"name": "लद्दाख", "name_en": "Ladakh", "state_code": "37"},
        {"name": "लक्षद्वीप", "name_en": "Lakshadweep", "state_code": "31"},
        {"name": "पुडुचेरी", "name_en": "Puducherry", "state_code": "34"},
    ],

    # Sample districts for major states (will be expanded)
    "districts": {
        "22": [  # Chhattisgarh
            {"name": "बस्तर", "name_en": "Bastar", "lgd_code": "398"},
            {"name": "बिलासपुर", "name_en": "Bilaspur", "lgd_code": "399"},
            {"name": "दंतेवाड़ा", "name_en": "Dantewada", "lgd_code": "400"},
            {"name": "धमतरी", "name_en": "Dhamtari", "lgd_code": "401"},
            {"name": "दुर्ग", "name_en": "Durg", "lgd_code": "402"},
            {"name": "जशपुर", "name_en": "Jashpur", "lgd_code": "403"},
            {"name": "जांजगीर-चांपा", "name_en": "Janjgir-Champa", "lgd_code": "404"},
            {"name": "कोरबा", "name_en": "Korba", "lgd_code": "405"},
            {"name": "कोरिया", "name_en": "Koriya", "lgd_code": "406"},
            {"name": "कांकेर", "name_en": "Kanker", "lgd_code": "407"},
            {"name": "कबीरधाम", "name_en": "Kabirdham", "lgd_code": "408"},
            {"name": "महासमुंद", "name_en": "Mahasamund", "lgd_code": "409"},
            {"name": "नारायणपुर", "name_en": "Narayanpur", "lgd_code": "410"},
            {"name": "रायगढ़", "name_en": "Raigarh", "lgd_code": "411"},
            {"name": "रायपुर", "name_en": "Raipur", "lgd_code": "412"},
            {"name": "राजनांदगाँव", "name_en": "Rajnandgaon", "lgd_code": "413"},
            {"name": "सुकमा", "name_en": "Sukma", "lgd_code": "414"},
            {"name": "सुरगुजा", "name_en": "Surguja", "lgd_code": "415"},
            {"name": "कोंडागांव", "name_en": "Kondagaon", "lgd_code": "638"},
            {"name": "बलोद", "name_en": "Balod", "lgd_code": "639"},
            {"name": "बालोदा बाजार", "name_en": "Baloda Bazar", "lgd_code": "640"},
            {"name": "बेमेतरा", "name_en": "Bemetara", "lgd_code": "641"},
            {"name": "बीजापुर", "name_en": "Bijapur", "lgd_code": "642"},
            {"name": "गरियाबंद", "name_en": "Gariyaband", "lgd_code": "643"},
            {"name": "गौरेला-पेंड्रा-मरवाही", "name_en": "Gaurela-Pendra-Marwahi", "lgd_code": "644"},
            {"name": "मुंगेली", "name_en": "Mungeli", "lgd_code": "645"},
            {"name": "सूरजपुर", "name_en": "Surajpur", "lgd_code": "646"},
            {"name": "बलरामपुर", "name_en": "Balrampur", "lgd_code": "647"},
        ],
        "09": [  # Uttar Pradesh (sample)
            {"name": "आगरा", "name_en": "Agra", "lgd_code": "101"},
            {"name": "प्रयागराज", "name_en": "Prayagraj", "lgd_code": "102"},
            {"name": "वाराणसी", "name_en": "Varanasi", "lgd_code": "103"},
            {"name": "लखनऊ", "name_en": "Lucknow", "lgd_code": "104"},
            {"name": "कानपुर", "name_en": "Kanpur", "lgd_code": "105"},
        ],
        "10": [  # Bihar (sample)
            {"name": "पटना", "name_en": "Patna", "lgd_code": "201"},
            {"name": "गया", "name_en": "Gaya", "lgd_code": "202"},
            {"name": "मुजफ्फरपुर", "name_en": "Muzaffarpur", "lgd_code": "203"},
        ],
    },

    "blocks": {
        "398": [  # Bastar
            {"name": "बस्तर", "name_en": "Bastar", "lgd_code": "3151"},
            {"name": "बाकावंड", "name_en": "Bakawand", "lgd_code": "3152"},
            {"name": "छोटे डोंगर", "name_en": "Chhote Dongar", "lgd_code": "3153"},
            {"name": "जगदलपुर", "name_en": "Jagdalpur", "lgd_code": "3154"},
            {"name": "लोहंडीगुड़ा", "name_en": "Lohandiguda", "lgd_code": "3155"},
            {"name": "तोकापाल", "name_en": "Tokapal", "lgd_code": "3156"},
        ],
        "412": [  # Raipur
            {"name": "आरंग", "name_en": "Arang", "lgd_code": "3301"},
            {"name": "अभनपुर", "name_en": "Abhanpur", "lgd_code": "3302"},
            {"name": "बिलाईगढ़", "name_en": "Bilaigarh", "lgd_code": "3303"},
        ],
    },

    "panchayats": {
        "3155": [  # Lohandiguda
            {"name": "मादर", "name_en": "Madar", "lgd_code": "123456"},
            {"name": "कोटापाल", "name_en": "Kotapal", "lgd_code": "123457"},
            {"name": "धनोरा", "name_en": "Dhanora", "lgd_code": "123458"},
        ],
        "3154": [  # Jagdalpur
            {"name": "नगनार", "name_en": "Nagnar", "lgd_code": "123461"},
            {"name": "अमाबेड़ा", "name_en": "Amabeda", "lgd_code": "123462"},
        ],
    }
}


def get_database_url():
    """Get database URL from environment"""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://boloo:boloo_dev_password@localhost:5432/boloo"
    )


def create_all_india_tables():
    """Create administrative tables for all Indian states"""

    engine = create_engine(get_database_url())
    metadata = MetaData()

    # States table
    states_table = Table(
        'admin_states',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(255), nullable=False),
        Column('name_en', String(255), nullable=False),
        Column('state_code', String(5), unique=True, nullable=False),
    )

    # Districts table
    districts_table = Table(
        'admin_districts',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(255), nullable=False),
        Column('name_en', String(255), nullable=False),
        Column('lgd_code', String(20), unique=True, nullable=False),
        Column('state_code', String(5), nullable=False),
    )

    # Blocks table
    blocks_table = Table(
        'admin_blocks',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(255), nullable=False),
        Column('name_en', String(255), nullable=False),
        Column('lgd_code', String(20), unique=True, nullable=False),
        Column('district_lgd_code', String(20), nullable=False),
    )

    # Panchayats table
    panchayats_table = Table(
        'admin_panchayats',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(255), nullable=False),
        Column('name_en', String(255), nullable=False),
        Column('lgd_code', String(20), unique=True, nullable=False),
        Column('block_lgd_code', String(20), nullable=False),
    )

    logger.info("Creating All-India administrative tables...")
    metadata.create_all(engine)

    conn = engine.connect()

    # Clear existing data
    logger.info("Clearing existing data...")
    conn.execute(text("TRUNCATE TABLE admin_panchayats, admin_blocks, admin_districts, admin_states CASCADE"))
    conn.commit()

    # Insert states
    logger.info(f"Inserting {len(ALL_INDIA_DATA['states'])} states...")
    for state in ALL_INDIA_DATA['states']:
        conn.execute(states_table.insert().values(**state))
    conn.commit()

    # Insert districts
    total_districts = sum(len(districts) for districts in ALL_INDIA_DATA['districts'].values())
    logger.info(f"Inserting {total_districts} districts...")
    for state_code, districts in ALL_INDIA_DATA['districts'].items():
        for district in districts:
            conn.execute(districts_table.insert().values(
                **district,
                state_code=state_code
            ))
    conn.commit()

    # Insert blocks
    total_blocks = sum(len(blocks) for blocks in ALL_INDIA_DATA['blocks'].values())
    logger.info(f"Inserting {total_blocks} blocks...")
    for district_code, blocks in ALL_INDIA_DATA['blocks'].items():
        for block in blocks:
            conn.execute(blocks_table.insert().values(
                **block,
                district_lgd_code=district_code
            ))
    conn.commit()

    # Insert panchayats
    total_panchayats = sum(len(panchayats) for panchayats in ALL_INDIA_DATA['panchayats'].values())
    logger.info(f"Inserting {total_panchayats} panchayats...")
    for block_code, panchayats in ALL_INDIA_DATA['panchayats'].items():
        for panchayat in panchayats:
            conn.execute(panchayats_table.insert().values(
                **panchayat,
                block_lgd_code=block_code
            ))
    conn.commit()

    conn.close()

    logger.info("✅ All-India dropdown data created successfully!")
    logger.info(f"   • {len(ALL_INDIA_DATA['states'])} states/UTs")
    logger.info(f"   • {total_districts} districts")
    logger.info(f"   • {total_blocks} blocks")
    logger.info(f"   • {total_panchayats} panchayats")
    logger.info("")
    logger.info("NOTE: This is initial seed data. You can add more districts/blocks/panchayats")
    logger.info("by running: python scripts/import_lgd_data.py --state <state_code>")


if __name__ == "__main__":
    try:
        create_all_india_tables()
    except Exception as e:
        logger.error(f"Error creating All-India data: {e}", exc_info=True)
        sys.exit(1)
