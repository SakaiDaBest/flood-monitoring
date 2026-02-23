from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.risk import classify_risk, check_rapid_rise, create_or_update_incident, should_escalate
from app.services.alerts import send_telegram_alert
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class ReadingCreate(BaseModel):
    device_id: str
    water_level_cm: float
    timestamp: Optional[datetime] = None

class ReadingOut(BaseModel):
    id: int
    device_id: str
    water_level: float
    risk_level: str
    timestamp: datetime

    class Config:
        from_attributes = True

async def process_alert(device_id: str, water_level: float, risk, rapid_rise: bool, db: Session):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if device and risk != models.RiskLevel.SAFE:
        await send_telegram_alert(
            device_id=device_id,
            device_name=device.name,
            location=device.location,
            water_level=water_level,
            risk=risk,
            rapid_rise=rapid_rise,
        )

@router.post("/", response_model=ReadingOut)
async def submit_reading(reading: ReadingCreate, background_tasks: BackgroundTasks,
                         db: Session = Depends(get_db)):
    # Verify device exists
    device = db.query(models.Device).filter(models.Device.id == reading.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{reading.device_id}' not found. Register it first.")

    # Classify risk
    risk = classify_risk(reading.water_level_cm)
    rapid_rise = check_rapid_rise(db, reading.device_id, reading.water_level_cm)

    # If rapid rise, escalate risk level
    if rapid_rise and risk == models.RiskLevel.WARNING:
        risk = models.RiskLevel.HIGH_RISK

    # Store reading
    db_reading = models.Reading(
        device_id=reading.device_id,
        water_level=reading.water_level_cm,
        risk_level=risk,
        timestamp=reading.timestamp or datetime.utcnow(),
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)

    # Create/update incident
    incident = create_or_update_incident(db, reading.device_id, risk, rapid_rise)

    # Send alert in background if new incident or critical
    if incident or risk == models.RiskLevel.CRITICAL:
        background_tasks.add_task(process_alert, reading.device_id, reading.water_level_cm, risk, rapid_rise, db)

    return db_reading

@router.get("/", response_model=List[ReadingOut])
def list_readings(device_id: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(models.Reading)
    if device_id:
        query = query.filter(models.Reading.device_id == device_id)
    return query.order_by(models.Reading.timestamp.desc()).limit(limit).all()

@router.get("/latest/{device_id}", response_model=ReadingOut)
def latest_reading(device_id: str, db: Session = Depends(get_db)):
    reading = (
        db.query(models.Reading)
        .filter(models.Reading.device_id == device_id)
        .order_by(models.Reading.timestamp.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found for this device")
    return reading
