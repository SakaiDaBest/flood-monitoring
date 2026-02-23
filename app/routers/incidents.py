from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class IncidentOut(BaseModel):
    id: int
    device_id: str
    risk_level: str
    triggered_at: datetime
    resolved_at: Optional[datetime]
    message: Optional[str]

    class Config:
        from_attributes = True

@router.get("/", response_model=List[IncidentOut])
def list_incidents(device_id: Optional[str] = None, open_only: bool = False,
                   db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(models.Incident)
    if device_id:
        query = query.filter(models.Incident.device_id == device_id)
    if open_only:
        query = query.filter(models.Incident.resolved_at == None)
    return query.order_by(models.Incident.triggered_at.desc()).limit(100).all()
