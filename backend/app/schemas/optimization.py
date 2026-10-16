from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.dead_zone import DeadZoneOut

class APRecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_id: int
    floor_id: int
    candidate_x: float
    candidate_y: float
    tx_power_dbm: float
    priority: int
    reason: str
    expected_dead_zone_reduction_area: float
    expected_dead_zone_count_reduction: int
    expected_coverage_gain_pct: float
    created_at: datetime

class APRecommendationRequest(BaseModel):
    floor_id: int
    run_id: int
    max_recommendations: Optional[int] = 3

class BeforeAfterComparisonOut(BaseModel):
    floor_id: int
    baseline_run_id: int
    optimized_run_id: int

    # Dead zone metrics
    before_dead_zone_count: int
    after_dead_zone_count: int
    dead_zone_count_reduction: int
    dead_zone_count_reduction_pct: float

    before_dead_zone_area: float
    after_dead_zone_area: float
    dead_zone_area_reduction: float
    dead_zone_area_reduction_pct: float

    # Coverage percentage
    before_coverage_good_pct: float
    after_coverage_good_pct: float
    before_coverage_poor_pct: float
    after_coverage_poor_pct: float

    # Signal quality metrics
    before_avg_rssi: float
    after_avg_rssi: float
    rssi_improvement: float

    before_avg_latency: float
    after_avg_latency: float
    latency_reduction: float

    before_avg_packet_loss: float
    after_avg_packet_loss: float
    packet_loss_reduction: float

    before_avg_throughput: float
    after_avg_throughput: float
    throughput_improvement: float

    # Status indicators
    status: Optional[str] = "IMPROVED"
    area_reduction_status: Optional[str] = "IMPROVED"

    recommended_aps_added: List[APRecommendationOut]
    before_dead_zones: List[DeadZoneOut]
    after_dead_zones: List[DeadZoneOut]
