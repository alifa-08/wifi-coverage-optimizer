from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class SurveySession(Base):
    __tablename__ = "survey_sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="ACTIVE") # ACTIVE, COMPLETED
    floorplan_image_path = Column(String(255), nullable=True) # Optional uploaded floorplan image
    floorplan_width_m = Column(Float, default=80.0)
    floorplan_height_m = Column(Float, default=50.0)
    ping_target = Column(String(100), default="auto") # Gateway or custom IP
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    measurements = relationship("SurveyMeasurement", back_populates="survey", cascade="all, delete-orphan")


class SurveyMeasurement(Base):
    __tablename__ = "survey_measurements"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("survey_sessions.id", ondelete="CASCADE"), nullable=False)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)

    # Floorplan coordinates (in meters)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Actual Windows Wi-Fi telemetry
    ssid = Column(String(100), nullable=True)
    bssid = Column(String(50), nullable=True)
    signal_value = Column(Float, nullable=True)          # Raw Windows reported signal (e.g. 92.0)
    signal_unit = Column(String(10), default="%")        # "%" or "dBm"
    rssi_estimated_dbm = Column(Float, nullable=True)    # Estimated dBm: (signal_pct / 2) - 100, or raw hardware RSSI
    is_rssi_estimated = Column(Boolean, default=True)    # True if calculated, False if hardware dBm
    channel = Column(Integer, nullable=True)
    band = Column(String(20), nullable=True)             # "2.4 GHz", "5 GHz", "6 GHz"
    radio_type = Column(String(30), nullable=True)       # "802.11ax", "802.11ac", etc.
    link_speed_mbps = Column(Float, nullable=True)       # Windows reported link speed (Rx/Tx rate)

    # Actual Network ping test
    latency_ms = Column(Float, nullable=True)
    packet_loss_percent = Column(Float, nullable=True)
    ping_target = Column(String(100), nullable=True)
    ping_target_type = Column(String(30), default="local_gateway") # local_gateway, internet, custom

    # Composite category
    quality_score = Column(Float, default=50.0)
    quality_category = Column(String(20), default="MODERATE") # GOOD, MODERATE, POOR

    # Strict academic distinction
    is_synthetic = Column(Boolean, default=False)        # False for real survey data!
    measurement_source = Column(String(50), default="windows_netsh_survey")
    notes = Column(Text, nullable=True)

    survey = relationship("SurveySession", back_populates="measurements")
