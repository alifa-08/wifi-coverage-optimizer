from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class AccessPoint(Base):
    __tablename__ = "access_points"

    id = Column(Integer, primary_key=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    tx_power_dbm = Column(Float, default=20.0)
    frequency_ghz = Column(Float, default=2.4)
    channel = Column(Integer, default=6)
    ssid = Column(String(50), default="Campus-Wi-Fi")
    is_active = Column(Boolean, default=True)
    is_recommended = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    floor = relationship("Floor", back_populates="access_points")


class APRecommendation(Base):
    __tablename__ = "ap_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    candidate_x = Column(Float, nullable=False)
    candidate_y = Column(Float, nullable=False)
    tx_power_dbm = Column(Float, default=20.0)
    priority = Column(Integer, default=1)  # 1 = highest
    reason = Column(Text, nullable=False)
    expected_dead_zone_reduction_area = Column(Float, default=0.0) # m^2
    expected_dead_zone_count_reduction = Column(Integer, default=0)
    expected_coverage_gain_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
