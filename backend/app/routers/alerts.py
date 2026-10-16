from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertOut, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertOut])
@router.get("/", response_model=List[AlertOut])
def list_alerts(status: str = None, db: Session = Depends(get_db)):

    """List network alerts filtered optionally by status (ACTIVE / RESOLVED)."""
    query = db.query(Alert).order_by(Alert.id.desc())
    if status:
        query = query.filter(Alert.status == status.upper())
    return query.all()

@router.put("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Resolve an active alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "RESOLVED"
    alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert
