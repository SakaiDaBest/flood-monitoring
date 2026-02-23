from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.auth import get_current_user
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter()

class DeviceCreate(BaseModel):
    id: str
    name: str
    location: str

class DeviceOut(BaseModel):
    id: str
    name: str
    location: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    return db.query(models.Device).all()

@router.post("/", response_model=DeviceOut)
def create_device(device: DeviceCreate, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    existing = db.query(models.Device).filter(models.Device.id == device.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device ID already exists")
    db_device = models.Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
