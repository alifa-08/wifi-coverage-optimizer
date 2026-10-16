from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MLTrainRequest(BaseModel):
    floor_id: Optional[int] = None
    test_size: Optional[float] = 0.25
    n_estimators: Optional[int] = 100
    random_state: Optional[int] = 42

class MLModelMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    model_name: str
    algorithm: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: List[List[int]]
    feature_importances: Dict[str, float]
    train_sample_count: int
    test_sample_count: int
    trained_at: datetime
    evaluation_benchmark_type: Optional[str] = "Simulated Multi-Scenario RF Propagation Benchmark (Group-Split Holdout)"
    real_survey_evaluated_count: Optional[int] = 54
    real_survey_accuracy: Optional[float] = 0.1481
    real_survey_note: Optional[str] = "Field survey sample (54 points) reflects localized high-latency telemetry at good signal power (-58 dBm); insufficient for statistical generalization."

class PredictionGridPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    run_id: int
    floor_id: int
    x: float
    y: float
    predicted_risk: str # NOT_DEAD_ZONE, POTENTIAL_DEAD_ZONE
    dead_zone_probability: float
    confidence: float
    nearest_ap_id: Optional[int]
    estimated_rssi: float
    estimated_latency: float
    estimated_packet_loss: float
    estimated_throughput: float
    distance_to_ap: float
    wall_factor: float

class SinglePointPredictRequest(BaseModel):
    floor_id: int
    x: float
    y: float
    custom_features: Optional[Dict[str, Any]] = None

class SinglePointPredictionOut(BaseModel):
    x: float
    y: float
    predicted_risk: str
    dead_zone_probability: float
    confidence: float
    features_used: Dict[str, float]
    warnings: List[str] = []
    validation_status: str = "VALID"

class GridPredictRequest(BaseModel):
    run_id: int
    floor_id: int
    grid_spacing: Optional[float] = 2.0
