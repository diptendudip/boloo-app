"""Entities router"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Entity

router = APIRouter()

@router.get("")
async def list_entities(db: Session = Depends(get_db)):
    """List all entities"""
    entities = db.query(Entity).filter(Entity.is_active == True).all()
    return {"entities": [e.to_dict() for e in entities]}

@router.get("/{entity_id}")
async def get_entity(entity_id: str, db: Session = Depends(get_db)):
    """Get entity by ID"""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        return {"error": "Entity not found"}, 404
    return {"entity": entity.to_dict()}
