from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MeasurementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_id: int
    floor_id: int
    ap_id: Optional[int]
    timestamp: datetime
    x: float
    y: float
    rssi: float
    latency: float
    packet_loss: float
    throughput: float
    distance_to_ap: float
    wall_factor: float
    quality_score: float
    quality_category: str

class SimulationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    floor_id: int
    name: str
    scenario_name: str
    total_points: int
    is_baseline: bool
    created_at: datetime

class SimulationRunRequest(BaseModel):
    floor_id: int
    scenario_name: Optional[str] = "Standard"
    grid_spacing: Optional[float] = 2.0  # meters between simulated sample points
    include_noise: Optional[bool] = True
    save_to_db: Optional[bool] = True
