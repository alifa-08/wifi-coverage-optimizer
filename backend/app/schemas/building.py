from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class RoomBase(BaseModel):
    name: str
    room_type: str
    x1: float
    y1: float
    x2: float
    y2: float
    color: Optional[str] = "#e2e8f0"

class RoomCreate(RoomBase):
    floor_id: int

class RoomOut(RoomBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    floor_id: int


class WallBase(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    wall_type: Optional[str] = "concrete"
    attenuation_db: Optional[float] = 12.0

class WallCreate(WallBase):
    floor_id: int

class WallOut(WallBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    floor_id: int

class AccessPointBase(BaseModel):
    name: str
    x: float
    y: float
    tx_power_dbm: Optional[float] = 20.0
    frequency_ghz: Optional[float] = 2.4
    channel: Optional[int] = 6
    ssid: Optional[str] = "Campus-Wi-Fi"
    is_active: Optional[bool] = True
    is_recommended: Optional[bool] = False

class AccessPointCreate(AccessPointBase):
    floor_id: int

class AccessPointOut(AccessPointBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    floor_id: int
    created_at: datetime

class FloorBase(BaseModel):
    floor_number: int
    name: str
    height_meters: Optional[float] = 3.5

class FloorOut(FloorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    building_id: int
    rooms: List[RoomOut] = []
    walls: List[WallOut] = []
    access_points: List[AccessPointOut] = []

class BuildingBase(BaseModel):
    name: str
    description: Optional[str] = None
    width: float = 80.0
    height: float = 50.0

class BuildingCreate(BuildingBase):
    pass

class BuildingOut(BuildingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    floors: List[FloorOut] = []
