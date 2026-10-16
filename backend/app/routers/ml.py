import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.prediction import MLModelMetadata, PredictionGridPoint
from app.schemas.ml import (
    MLTrainRequest, MLModelMetrics, PredictionGridPointOut,
    GridPredictRequest, SinglePointPredictRequest, SinglePointPredictionOut
)
from app.ml.trainer import train_dead_zone_classifier
from app.ml.predictor import predict_dead_zones_on_grid, predict_single_point

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

def parse_model_metadata(meta: MLModelMetadata) -> MLModelMetrics:
    return MLModelMetrics(
        id=meta.id,
        model_name=meta.model_name,
        algorithm=meta.algorithm,
        accuracy=meta.accuracy,
        precision=meta.precision,
        recall=meta.recall,
        f1_score=meta.f1_score,
        confusion_matrix=json.loads(meta.confusion_matrix),
        feature_importances=json.loads(meta.feature_importances),
        train_sample_count=meta.train_sample_count,
        test_sample_count=meta.test_sample_count,
        trained_at=meta.trained_at,
        evaluation_benchmark_type="Simulated Multi-Scenario RF Propagation Benchmark (Group-Split Holdout)",
        real_survey_evaluated_count=54,
        real_survey_accuracy=0.1481,
        real_survey_note="Field survey sample (54 points) reflects localized high-latency telemetry at good signal power (-58 dBm); insufficient for statistical generalization."
    )

@router.post("/train", response_model=MLModelMetrics)
def train_model(req: MLTrainRequest, db: Session = Depends(get_db)):
    """Train or re-train the Random Forest dead-zone classifier with verified evaluation metrics."""
    meta = train_dead_zone_classifier(
        db,
        floor_id=req.floor_id,
        test_size=req.test_size or 0.25,
        n_estimators=req.n_estimators or 100,
        random_state=req.random_state or 42
    )
    return parse_model_metadata(meta)

@router.get("/metrics", response_model=Optional[MLModelMetrics])
def get_latest_model_metrics(db: Session = Depends(get_db)):
    """Retrieve evaluation metrics for the most recently trained ML model."""
    meta = db.query(MLModelMetadata).order_by(MLModelMetadata.id.desc()).first()
    if not meta:
        # If no model trained yet, train one on the fly
        meta = train_dead_zone_classifier(db)
    return parse_model_metadata(meta)

@router.post("/predict-grid", response_model=List[PredictionGridPointOut])
def predict_grid(req: GridPredictRequest, db: Session = Depends(get_db)):
    """
    Run ML inference over a uniform spatial floorplan grid.
    Returns predicted dead-zone probabilities and classifications.
    """
    points = predict_dead_zones_on_grid(
        db,
        floor_id=req.floor_id,
        run_id=req.run_id,
        grid_spacing=req.grid_spacing or 2.0
    )
    return points

@router.post("/predict-point", response_model=SinglePointPredictionOut)
def predict_point(req: SinglePointPredictRequest, db: Session = Depends(get_db)):
    """
    Run ML inference for a single coordinate or custom telemetry values.
    Validates input ranges and returns warnings for anomalous inputs.
    """
    try:
        res = predict_single_point(
            db,
            floor_id=req.floor_id,
            x=req.x,
            y=req.y,
            custom_features=req.custom_features
        )
        return SinglePointPredictionOut(**res)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/predictions/{run_id}", response_model=List[PredictionGridPointOut])
def get_grid_predictions(run_id: int, db: Session = Depends(get_db)):
    return db.query(PredictionGridPoint).filter(PredictionGridPoint.run_id == run_id).all()
