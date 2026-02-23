from app.models import RiskLevel
from sqlalchemy.orm import Session
from app import models
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def classify_risk(water_level: float) -> RiskLevel:
    if water_level < 30:
        return RiskLevel.SAFE
    elif water_level < 60:
        return RiskLevel.WARNING
    elif water_level < 90:
        return RiskLevel.HIGH_RISK
    else:
        return RiskLevel.CRITICAL

def check_rapid_rise(db: Session, device_id: str, current_level: float) -> bool:
    """Returns True if water rose more than 15cm in last 10 minutes."""
    ten_mins_ago = datetime.utcnow() - timedelta(minutes=10)
    oldest_recent = (
        db.query(models.Reading)
        .filter(
            models.Reading.device_id == device_id,
            models.Reading.timestamp >= ten_mins_ago,
        )
        .order_by(models.Reading.timestamp.asc())
        .first()
    )
    if oldest_recent and (current_level - oldest_recent.water_level) > 15:
        logger.warning(f"Rapid rise detected for {device_id}: +{current_level - oldest_recent.water_level:.1f}cm in 10 min")
        return True
    return False

def should_escalate(db: Session, device_id: str, risk: RiskLevel) -> bool:
    """Check if current risk has been persisting long enough to escalate."""
    now = datetime.utcnow()
    if risk == RiskLevel.WARNING:
        threshold = now - timedelta(minutes=30)
    elif risk == RiskLevel.HIGH_RISK:
        threshold = now - timedelta(minutes=10)
    else:
        return False

    # Check if there's an open incident older than threshold
    incident = (
        db.query(models.Incident)
        .filter(
            models.Incident.device_id == device_id,
            models.Incident.risk_level == risk,
            models.Incident.triggered_at <= threshold,
            models.Incident.resolved_at == None,
        )
        .first()
    )
    return incident is not None

def create_or_update_incident(db: Session, device_id: str, risk: RiskLevel, rapid_rise: bool = False) -> None:
    if risk == RiskLevel.SAFE:
        # Resolve any open incidents for this device
        open_incidents = (
            db.query(models.Incident)
            .filter(
                models.Incident.device_id == device_id,
                models.Incident.resolved_at == None,
            )
            .all()
        )
        for inc in open_incidents:
            inc.resolved_at = datetime.utcnow()
            logger.info(f"Resolved incident #{inc.id} for {device_id}")
        db.commit()
        return

    # Check if there's already an open incident at this level
    existing = (
        db.query(models.Incident)
        .filter(
            models.Incident.device_id == device_id,
            models.Incident.risk_level == risk,
            models.Incident.resolved_at == None,
        )
        .first()
    )

    if not existing:
        msg = f"Water level crossed {risk.value} threshold"
        if rapid_rise:
            msg += " (RAPID RISE detected)"
        incident = models.Incident(
            device_id=device_id,
            risk_level=risk,
            message=msg,
        )
        db.add(incident)
        db.commit()
        logger.warning(f"New incident created for {device_id}: {risk.value}")
        return incident
