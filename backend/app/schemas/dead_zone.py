from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DeadZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_id: int
    floor_id: int
    name: str
    center_x: float
    center_y: float
    bounding_box: Dict[str, float]
    polygon_points: List[List[float]]
    affected_area: float
    severity: str
    num_measurements: int
    avg_rssi: float
    avg_latency: float
    avg_packet_loss: float
    avg_throughput: float
    nearest_ap_id: Optional[int]
    contributing_factors: List[str]
    persistence_score: float
    is_persistent: bool
    created_at: datetime

class DeadZoneDetectionRequest(BaseModel):
    run_id: int
    min_samples: Optional[int] = 3
    eps_distance: Optional[float] = 6.0 # clustering radius in meters
    rssi_threshold: Optional[float] = -78.0
