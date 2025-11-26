"""Taxonomies router"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Taxonomy

router = APIRouter()

@router.get("")
async def list_taxonomies(
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List taxonomies"""
    query = db.query(Taxonomy).filter(Taxonomy.is_active == True)
    if type:
        query = query.filter(Taxonomy.type == type)
    taxonomies = query.all()
    return {"taxonomies": [t.to_dict() for t in taxonomies]}
