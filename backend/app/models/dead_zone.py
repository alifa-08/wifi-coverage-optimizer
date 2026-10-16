from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class DeadZone(Base):
    __tablename__ = "dead_zones"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    center_x = Column(Float, nullable=False)
    center_y = Column(Float, nullable=False)
    bounding_box = Column(Text, nullable=False) # JSON string: {"min_x": .., "min_y": .., "max_x": .., "max_y": ..}
    polygon_points = Column(Text, nullable=False) # JSON string of [[x, y], ...]
    affected_area = Column(Float, nullable=False) # m^2
    severity = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    num_measurements = Column(Integer, nullable=False)
    avg_rssi = Column(Float, nullable=False)
    avg_latency = Column(Float, nullable=False)
    avg_packet_loss = Column(Float, nullable=False)
    avg_throughput = Column(Float, nullable=False)
    nearest_ap_id = Column(Integer, ForeignKey("access_points.id", ondelete="SET NULL"), nullable=True)
    contributing_factors = Column(Text, nullable=False) # JSON string list of reasons
    persistence_score = Column(Float, default=0.0) # 0.0 - 1.0
    is_persistent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("SimulationRun", back_populates="dead_zones")
    observations = relationship("DeadZoneObservation", back_populates="dead_zone", cascade="all, delete-orphan")


class DeadZoneObservation(Base):
    __tablename__ = "dead_zone_observations"

    id = Column(Integer, primary_key=True, index=True)
    dead_zone_id = Column(Integer, ForeignKey("dead_zones.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(Integer, ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    similarity_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    dead_zone = relationship("DeadZone", back_populates="observations")
