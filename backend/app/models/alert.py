from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False) # SEVERE_DEAD_ZONE, PERSISTENT_DEAD_ZONE, COVERAGE_DROP, CAPACITY_RISK
    severity = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    dead_zone_id = Column(Integer, ForeignKey("dead_zones.id", ondelete="SET NULL"), nullable=True)
    location_x = Column(Float, nullable=True)
    location_y = Column(Float, nullable=True)
    status = Column(String(20), default="ACTIVE") # ACTIVE, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
