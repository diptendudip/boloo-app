"""
Dropdown API endpoints for cascading location selection

Provides hierarchical dropdown data:
State → District → Block → Panchayat

All states across India are supported.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dropdown", tags=["dropdown"])


@router.get("/states")
async def get_states(
    db: Session = Depends(get_db)
):
    """
    Get list of all Indian states and UTs

    Returns:
        List of states with Hindi and English names
    """
    try:
        query = text("""
            SELECT id, name, name_en, state_code
            FROM admin_states
            ORDER BY name_en
        """)

        result = db.execute(query).fetchall()

        states = [
            {
                "id": row[0],
                "name": row[1],
                "name_en": row[2],
                "state_code": row[3]
            }
            for row in result
        ]

        logger.info(f"Returning {len(states)} states")
        return {"states": states}

    except Exception as e:
        logger.error(f"Error fetching states: {e}", exc_info=True)
        return {"states": []}


@router.get("/districts")
async def get_districts(
    state_code: str = Query(..., description="State code (e.g., 22 for Chhattisgarh)"),
    db: Session = Depends(get_db)
):
    """
    Get list of districts for a given state

    Args:
        state_code: Two-digit state code

    Returns:
        List of districts with Hindi and English names
    """
    try:
        query = text("""
            SELECT id, name, name_en, lgd_code, state_code
            FROM admin_districts
            WHERE state_code = :state_code
            ORDER BY name_en
        """)

        result = db.execute(query, {"state_code": state_code}).fetchall()

        districts = [
            {
                "id": row[0],
                "name": row[1],
                "name_en": row[2],
                "lgd_code": row[3],
                "state_code": row[4]
            }
            for row in result
        ]

        logger.info(f"Returning {len(districts)} districts for state {state_code}")
        return {"districts": districts}

    except Exception as e:
        logger.error(f"Error fetching districts: {e}", exc_info=True)
        return {"districts": []}


@router.get("/blocks")
async def get_blocks(
    district_lgd_code: str = Query(..., description="District LGD code"),
    db: Session = Depends(get_db)
):
    """
    Get list of blocks for a given district

    Args:
        district_lgd_code: LGD code of the district

    Returns:
        List of blocks with Hindi and English names
    """
    try:
        query = text("""
            SELECT id, name, name_en, lgd_code, district_lgd_code
            FROM admin_blocks
            WHERE district_lgd_code = :district_lgd_code
            ORDER BY name_en
        """)

        result = db.execute(query, {"district_lgd_code": district_lgd_code}).fetchall()

        blocks = [
            {
                "id": row[0],
                "name": row[1],
                "name_en": row[2],
                "lgd_code": row[3],
                "district_lgd_code": row[4]
            }
            for row in result
        ]

        logger.info(f"Returning {len(blocks)} blocks for district {district_lgd_code}")
        return {"blocks": blocks}

    except Exception as e:
        logger.error(f"Error fetching blocks: {e}", exc_info=True)
        return {"blocks": []}


@router.get("/panchayats")
async def get_panchayats(
    block_lgd_code: str = Query(..., description="Block LGD code"),
    db: Session = Depends(get_db)
):
    """
    Get list of panchayats for a given block

    Args:
        block_lgd_code: LGD code of the block

    Returns:
        List of panchayats with Hindi and English names
    """
    try:
        query = text("""
            SELECT id, name, name_en, lgd_code, block_lgd_code
            FROM admin_panchayats
            WHERE block_lgd_code = :block_lgd_code
            ORDER BY name_en
        """)

        result = db.execute(query, {"block_lgd_code": block_lgd_code}).fetchall()

        panchayats = [
            {
                "id": row[0],
                "name": row[1],
                "name_en": row[2],
                "lgd_code": row[3],
                "block_lgd_code": row[4]
            }
            for row in result
        ]

        logger.info(f"Returning {len(panchayats)} panchayats for block {block_lgd_code}")
        return {"panchayats": panchayats}

    except Exception as e:
        logger.error(f"Error fetching panchayats: {e}", exc_info=True)
        return {"panchayats": []}
