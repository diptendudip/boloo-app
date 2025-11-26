"""Admin router"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Case, User, Entity

router = APIRouter()

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    total_cases = db.query(func.count(Case.id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()
    total_entities = db.query(func.count(Entity.id)).scalar()

    cases_by_status = db.query(
        Case.status,
        func.count(Case.id)
    ).group_by(Case.status).all()

    return {
        "total_cases": total_cases,
        "total_users": total_users,
        "total_entities": total_entities,
        "cases_by_status": {status: count for status, count in cases_by_status}
    }
