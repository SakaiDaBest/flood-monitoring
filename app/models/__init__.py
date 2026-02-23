from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum

class RiskLevel(str, enum.Enum):
    SAFE = "safe"
    WARNING = "warning"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"

class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True)  # e.g. "river_001"
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    readings = relationship("Reading", back_populates="device")
    incidents = relationship("Incident", back_populates="device")

class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    water_level = Column(Float, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="readings")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    message = Column(String, nullable=True)

    device = relationship("Device", back_populates="incidents")

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
