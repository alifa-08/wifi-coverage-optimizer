from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from app.database import Base

class PredictionGridPoint(Base):
    __tablename__ = "prediction_grid_points"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    predicted_risk = Column(String(50), nullable=False) # NOT_DEAD_ZONE, POTENTIAL_DEAD_ZONE
    dead_zone_probability = Column(Float, nullable=False) # 0.0 - 1.0
    confidence = Column(Float, nullable=False)
    nearest_ap_id = Column(Integer, ForeignKey("access_points.id", ondelete="SET NULL"), nullable=True)
    estimated_rssi = Column(Float, nullable=False)
    estimated_latency = Column(Float, nullable=False)
    estimated_packet_loss = Column(Float, nullable=False)
    estimated_throughput = Column(Float, nullable=False)
    distance_to_ap = Column(Float, nullable=False)
    wall_factor = Column(Float, default=0.0)


class MLModelMetadata(Base):
    __tablename__ = "ml_model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    version = Column(String(20), default="1.0.0")
    algorithm = Column(String(100), default="RandomForestClassifier")
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    confusion_matrix = Column(Text, nullable=False) # JSON string: [[TN, FP], [FN, TP]]
    feature_importances = Column(Text, nullable=False) # JSON string: {feature: importance}
    train_sample_count = Column(Integer, nullable=False)
    test_sample_count = Column(Integer, nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String(255), nullable=False)
