from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    scenario_name = Column(String(100), default="Standard")
    total_points = Column(Integer, default=0)
    is_baseline = Column(Boolean, default=True)
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    floor = relationship("Floor", back_populates="simulation_runs")
    measurements = relationship("Measurement", back_populates="run", cascade="all, delete-orphan")
    dead_zones = relationship("DeadZone", back_populates="run", cascade="all, delete-orphan")


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    ap_id = Column(Integer, ForeignKey("access_points.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    rssi = Column(Float, nullable=False)                  # in dBm
    latency = Column(Float, nullable=False)               # in ms
    packet_loss = Column(Float, nullable=False)           # percentage (0-100)
    throughput = Column(Float, nullable=False)            # in Mbps
    distance_to_ap = Column(Float, nullable=False)        # in meters
    wall_factor = Column(Float, default=0.0)             # accumulated wall attenuation (dB)
    quality_score = Column(Float, nullable=False)         # 0 - 100 composite score
    quality_category = Column(String(20), nullable=False) # GOOD, MODERATE, POOR
    is_synthetic = Column(Boolean, default=True)          # True for simulated data, False for real survey data

    run = relationship("SimulationRun", back_populates="measurements")
