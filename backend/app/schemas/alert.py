from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    floor_id: int
    dead_zone_id: Optional[int]
    location_x: Optional[float]
    location_y: Optional[float]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]

class AlertUpdate(BaseModel):
    status: str
