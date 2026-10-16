from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    width = Column(Float, nullable=False, default=80.0)  # meters
    height = Column(Float, nullable=False, default=50.0) # meters
    created_at = Column(DateTime, default=datetime.utcnow)

    floors = relationship("Floor", back_populates="building", cascade="all, delete-orphan")


class Floor(Base):
    __tablename__ = "floors"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    floor_number = Column(Integer, nullable=False, default=1)
    name = Column(String(50), nullable=False, default="Ground Floor")
    height_meters = Column(Float, default=3.5)

    building = relationship("Building", back_populates="floors")
    rooms = relationship("Room", back_populates="floor", cascade="all, delete-orphan")
    walls = relationship("Wall", back_populates="floor", cascade="all, delete-orphan")
    access_points = relationship("AccessPoint", back_populates="floor", cascade="all, delete-orphan")
    simulation_runs = relationship("SimulationRun", back_populates="floor", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    room_type = Column(String(50), nullable=False)  # classroom, lab, office, corridor, reception, meeting_room
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    color = Column(String(20), default="#e2e8f0")

    floor = relationship("Floor", back_populates="rooms")


class Wall(Base):
    __tablename__ = "walls"

    id = Column(Integer, primary_key=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    wall_type = Column(String(50), default="concrete")  # concrete, drywall, glass, brick
    attenuation_db = Column(Float, default=12.0)  # attenuation in dB

    floor = relationship("Floor", back_populates="walls")
