from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.dead_zone import DeadZoneOut

class LiveWifiStatusOut(BaseModel):
    connected: bool
    state: Optional[str] = None
    ssid: Optional[str] = None
    bssid: Optional[str] = None
    signal_percent: Optional[float] = None
    signal_unit: str = "%"
    rssi_dbm: Optional[float] = None
    is_rssi_estimated: bool = True
    channel: Optional[int] = None
    band: Optional[str] = None
    radio_type: Optional[str] = None
    link_speed_mbps: Optional[float] = None
    latency_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    ping_target: Optional[str] = None
    ping_target_type: Optional[str] = None
    error: Optional[str] = None

class SurveyMeasurementBase(BaseModel):
    x: float
    y: float
    notes: Optional[str] = None

class SurveyMeasurementCreate(SurveyMeasurementBase):
    target_ip: Optional[str] = "auto"

class SurveyMeasurementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    survey_id: int
    building_id: int
    floor_id: int
    x: float
    y: float
    timestamp: datetime
    ssid: Optional[str] = None
    bssid: Optional[str] = None
    signal_value: Optional[float] = None
    signal_unit: str = "%"
    rssi_estimated_dbm: Optional[float] = None
    is_rssi_estimated: bool = True
    channel: Optional[int] = None
    band: Optional[str] = None
    radio_type: Optional[str] = None
    link_speed_mbps: Optional[float] = None
    latency_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    ping_target: Optional[str] = None
    ping_target_type: str = "local_gateway"
    quality_score: float = 50.0
    quality_category: str = "MODERATE"
    is_synthetic: bool = False
    measurement_source: str = "windows_netsh_survey"
    notes: Optional[str] = None

class SurveySessionBase(BaseModel):
    name: str
    building_id: int
    floor_id: int
    ping_target: Optional[str] = "auto"
    floorplan_width_m: Optional[float] = 80.0
    floorplan_height_m: Optional[float] = 50.0
    notes: Optional[str] = None

class SurveySessionCreate(SurveySessionBase):
    pass

class SurveySessionOut(SurveySessionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    floorplan_image_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    measurements: List[SurveyMeasurementOut] = []

class SurveyAnalysisOut(BaseModel):
    survey_id: int
    linked_simulation_run_id: int
    total_survey_points: int
    dead_zones: List[DeadZoneOut]
    density_warning: Optional[str] = None
    average_rssi_dbm: float
    average_latency_ms: float
    average_packet_loss_pct: float
    quality_breakdown: dict
