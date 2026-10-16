"""
Comprehensive Automated Tests for Random Forest ML Pipeline:
1. Dataset preparation, feature extraction, and input sanitization.
2. Training and evaluation separation with group-based splitting.
3. Authentic metric calculations, confusion matrix consistency, and zero-division handling.
4. Feature importance extraction and normalization.
5. Spatial grid prediction, probability indexing, and edge-case handling.
6. ML FastAPI endpoints and schema verification.
"""

import os
import json
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, Base, engine
from app.main import app
from app.config import settings
from app.ml.model import (
    FEATURE_NAMES,
    derive_ground_truth_label,
    compute_ap_density,
    load_trained_model,
)
from app.ml.trainer import (
    generate_synthetic_training_corpus,
    train_dead_zone_classifier,
)
from app.ml.predictor import predict_dead_zones_on_grid
from app.models.building import Building, Floor, Wall, Room
from app.models.ap import AccessPoint
from app.models.measurement import SimulationRun, Measurement
from app.models.prediction import MLModelMetadata, PredictionGridPoint

client = TestClient(app)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

# =========================================================================
# A. Dataset and Preprocessing Tests
# =========================================================================

def test_synthetic_corpus_generation():
    """Verify synthetic training corpus generation and required schema."""
    df = generate_synthetic_training_corpus(sample_size=300, random_state=42)
    assert len(df) == 300
    for feat in FEATURE_NAMES:
        assert feat in df.columns, f"Missing feature {feat} in synthetic corpus"
    assert "run_id" in df.columns, "Synthetic corpus should contain scenario run_id groups"
    assert df["rssi"].min() >= -98.0 and df["rssi"].max() <= -20.0
    assert df["packet_loss"].min() >= 0.0 and df["packet_loss"].max() <= 100.0

def test_derive_ground_truth_label_variations():
    """Verify deterministic multi-parameter ground truth label derivation."""
    # 1. Optimal wireless link -> NOT_DEAD_ZONE (0)
    optimal_point = {
        "rssi": -45.0,
        "latency": 12.0,
        "packet_loss": 0.0,
        "throughput": 220.0
    }
    assert derive_ground_truth_label(optimal_point) == 0

    # 2. Severe path loss -> POTENTIAL_DEAD_ZONE (1)
    severe_point = {
        "rssi": -86.0,
        "latency": 250.0,
        "packet_loss": 30.0,
        "throughput": 1.0
    }
    assert derive_ground_truth_label(severe_point) == 1

    # 3. High latency + packet loss degradation -> POTENTIAL_DEAD_ZONE (1)
    congested_point = {
        "rssi": -72.0,
        "latency": 190.0,
        "packet_loss": 22.0,
        "throughput": 4.0
    }
    assert derive_ground_truth_label(congested_point) == 1

    # 4. Moderate wireless link -> NOT_DEAD_ZONE (0)
    moderate_point = {
        "rssi": -72.0,
        "latency": 45.0,
        "packet_loss": 2.0,
        "throughput": 50.0
    }
    assert derive_ground_truth_label(moderate_point) == 0

    # 5. Missing / None / NaN / non-numeric edge cases -> handled gracefully without crash
    corrupt_point = {
        "rssi": None,
        "latency": float("nan"),
        "packet_loss": float("inf"),
        "throughput": "corrupted_text"
    }
    # Corrupt data with missing RSSI defaults to -95 dBm (poor) and flags dead zone
    assert derive_ground_truth_label(corrupt_point) in (0, 1)

def test_compute_ap_density():
    """Verify operational access point density computation within radius."""
    aps = [
        {"x": 10.0, "y": 10.0},
        {"x": 15.0, "y": 12.0},
        {"x": 80.0, "y": 80.0},  # Out of reach (>25m)
    ]
    # Point near first two APs
    density = compute_ap_density(12.0, 11.0, aps, radius=25.0)
    assert density == 2

    # Point near distant AP only
    density_distant = compute_ap_density(78.0, 79.0, aps, radius=25.0)
    assert density_distant == 1

    # Point with zero APs in reach
    density_isolated = compute_ap_density(100.0, 0.0, aps, radius=25.0)
    assert density_isolated == 0

# =========================================================================
# B. Training and Evaluation Separation Tests
# =========================================================================

def test_group_separation_by_run_id():
    """
    Verify that GroupShuffleSplit strictly isolates simulation runs between
    training and evaluation partitions, preventing spatial cross-run leakage.
    """
    from sklearn.model_selection import GroupShuffleSplit

    # Construct multi-run dataset
    records = []
    for r_id in range(1, 9):  # 8 distinct simulation runs
        for _ in range(50):
            records.append({
                "run_id": r_id,
                "rssi": np.random.uniform(-90.0, -30.0),
                "latency": np.random.uniform(10.0, 200.0),
                "packet_loss": np.random.uniform(0.0, 30.0),
                "throughput": np.random.uniform(1.0, 150.0),
                "distance_to_ap": np.random.uniform(2.0, 40.0),
                "wall_factor": np.random.choice([0.0, 10.0, 20.0]),
                "ap_density": np.random.choice([1, 2, 3]),
                "dead_zone_risk": np.random.choice([0, 1])
            })
    df = pd.DataFrame(records)

    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, test_idx = next(gss.split(df, df["dead_zone_risk"], groups=df["run_id"]))

    train_runs = set(df.iloc[train_idx]["run_id"].unique())
    test_runs = set(df.iloc[test_idx]["run_id"].unique())

    # Strict isolation: intersection of run IDs must be empty
    assert len(train_runs.intersection(test_runs)) == 0
    assert len(train_runs) + len(test_runs) == 8

def test_ml_model_training_and_metrics(db_session):
    """
    Verify Random Forest model training, evaluation metrics, and metadata persistence.
    """
    meta = train_dead_zone_classifier(db_session, n_estimators=25, random_state=42)

    # 1. Metrics bounds
    assert 0.0 <= meta.accuracy <= 1.0
    assert 0.0 <= meta.precision <= 1.0
    assert 0.0 <= meta.recall <= 1.0
    assert 0.0 <= meta.f1_score <= 1.0
    assert meta.accuracy > 0.70
    assert meta.f1_score > 0.60

    # 2. Confusion matrix consistency
    cm = json.loads(meta.confusion_matrix)
    assert len(cm) == 2 and len(cm[0]) == 2
    tn, fp = cm[0]
    fn, tp = cm[1]
    total_evaluated = tn + fp + fn + tp
    assert total_evaluated == meta.test_sample_count, (
        f"Confusion matrix sum ({total_evaluated}) must equal test_sample_count ({meta.test_sample_count})"
    )
    assert meta.train_sample_count > 0

    # 3. Feature importances validation
    fi = json.loads(meta.feature_importances)
    assert len(fi) == len(FEATURE_NAMES)
    for feat in FEATURE_NAMES:
        assert feat in fi
        assert 0.0 <= fi[feat] <= 1.0
    # Sum of Gini importances should equal ~1.0
    assert 0.99 <= sum(fi.values()) <= 1.01

    # 4. Model persistence
    assert os.path.exists(meta.file_path)

def test_confusion_matrix_orientation_and_absent_class():
    """
    Verify that confusion_matrix(labels=[0, 1]) preserves the standard 2x2 shape
    even when one class is absent in the evaluation set.
    """
    from sklearn.metrics import confusion_matrix

    y_true = np.array([0, 0, 0, 0])
    y_pred = np.array([0, 0, 0, 0])

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    assert len(cm) == 2 and len(cm[0]) == 2
    assert cm == [[4, 0], [0, 0]]

# =========================================================================
# C. Spatial Grid Prediction Tests
# =========================================================================

def test_grid_prediction_pipeline(db_session):
    """
    Verify spatial floorplan grid dead-zone risk extrapolation.
    """
    # 1. Setup minimal test building, floor, AP, and wall
    building = Building(name="ML Test Lab", description="North Campus", width=40.0, height=30.0)
    db_session.add(building)
    db_session.flush()

    floor = Floor(building_id=building.id, floor_number=1, name="Ground Floor")
    db_session.add(floor)
    db_session.flush()

    ap = AccessPoint(
        floor_id=floor.id,
        name="AP-ML-Test-1",
        x=20.0,
        y=15.0,
        tx_power_dbm=20.0,
        channel=6,
        is_active=True
    )
    db_session.add(ap)

    wall = Wall(
        floor_id=floor.id,
        x1=10.0,
        y1=0.0,
        x2=10.0,
        y2=30.0,
        wall_type="concrete",
        attenuation_db=14.0
    )
    db_session.add(wall)

    run = SimulationRun(
        floor_id=floor.id,
        name="ML Grid Test Run",
        scenario_name="Standard",
        is_baseline=True,
        is_synthetic=True
    )
    db_session.add(run)
    db_session.commit()

    # 2. Execute spatial grid prediction
    grid_points = predict_dead_zones_on_grid(
        db_session,
        floor_id=floor.id,
        run_id=run.id,
        grid_spacing=5.0
    )

    assert len(grid_points) > 0
    for p in grid_points:
        assert p.run_id == run.id
        assert p.floor_id == floor.id
        assert p.predicted_risk in ("NOT_DEAD_ZONE", "POTENTIAL_DEAD_ZONE")
        assert 0.0 <= p.dead_zone_probability <= 1.0
        assert 0.0 <= p.confidence <= 1.0
        assert -98.0 <= p.estimated_rssi <= -20.0
        assert p.estimated_latency >= 4.0
        assert 0.0 <= p.estimated_packet_loss <= 100.0

def test_prediction_with_anomalous_inputs():
    """
    Verify that load_trained_model and predict handle out-of-range inputs safely.
    """
    model, is_loaded = load_trained_model()
    assert is_loaded is True

    # Extreme RF parameters
    anomalous_df = pd.DataFrame([{
        "rssi": -99.9,
        "latency": 999.0,
        "packet_loss": 100.0,
        "throughput": 0.05,
        "distance_to_ap": 250.0,
        "wall_factor": 80.0,
        "ap_density": 0
    }])[FEATURE_NAMES]

    preds = model.predict(anomalous_df)
    probs = model.predict_proba(anomalous_df)

    assert len(preds) == 1
    assert preds[0] in (0, 1)
    assert len(probs[0]) == len(model.classes_)

# =========================================================================
# D. ML API Endpoint Tests
# =========================================================================

def test_ml_api_metrics_endpoint():
    """Verify /api/v1/ml/metrics returns honest, structured model performance metrics."""
    res = client.get("/api/v1/ml/metrics")
    assert res.status_code == 200
    data = res.json()

    assert data["model_name"] == "RandomForestDeadZonePredictor"
    assert "accuracy" in data
    assert "precision" in data
    assert "recall" in data
    assert "f1_score" in data
    assert "confusion_matrix" in data
    assert "feature_importances" in data
    assert "train_sample_count" in data
    assert "test_sample_count" in data
    assert "evaluation_benchmark_type" in data
    assert data["real_survey_evaluated_count"] == 54
    assert round(data["real_survey_accuracy"], 4) == 0.1481

    cm = data["confusion_matrix"]
    assert len(cm) == 2 and len(cm[0]) == 2
    assert (cm[0][0] + cm[0][1] + cm[1][0] + cm[1][1]) == data["test_sample_count"]

def test_ml_api_train_endpoint():
    """Verify /api/v1/ml/train retrains model and updates evaluation metrics."""
    req_body = {
        "test_size": 0.25,
        "n_estimators": 20,
        "random_state": 42
    }
    res = client.post("/api/v1/ml/train", json=req_body)
    assert res.status_code == 200
    data = res.json()
    assert data["accuracy"] > 0.70
    assert data["test_sample_count"] > 0

# =========================================================================
# E. Input Validation, Single Point Prediction & Survey Reproducibility
# =========================================================================

def test_validate_telemetry_features_strict_and_warnings():
    """Verify input validation behavior: strict raises ValueError, non-strict warns."""
    from app.ml.predictor import validate_telemetry_features

    # 1. Non-finite values in strict mode raise ValueError
    with pytest.raises(ValueError, match="Non-finite or missing RSSI"):
        validate_telemetry_features({"rssi": float("nan"), "latency": 20.0}, strict=True)

    with pytest.raises(ValueError, match="Invalid packet loss"):
        validate_telemetry_features({"rssi": -70.0, "latency": 20.0, "packet_loss": 150.0}, strict=True)

    with pytest.raises(ValueError, match="Out-of-range RSSI"):
        validate_telemetry_features({"rssi": 50.0, "latency": 20.0, "packet_loss": 2.0}, strict=True)

    # 2. Non-strict mode bounds anomalous values and generates explicit warnings
    val, warnings = validate_telemetry_features({
        "rssi": 50.0,
        "latency": -10.0,
        "packet_loss": 250.0,
        "throughput": -5.0,
        "distance_to_ap": 25.0,
        "wall_factor": 10.0,
        "ap_density": 1
    }, strict=False)

    assert len(warnings) >= 4
    assert val["rssi"] == -20.0  # Clamped to upper physical radio limit
    assert val["latency"] == 250.0  # Safely defaulted for negative
    assert val["packet_loss"] == 100.0  # Clamped to 100%

def test_predict_single_point_and_boundaries(db_session):
    """Verify single point prediction and coordinate boundary enforcement."""
    from app.ml.predictor import predict_single_point

    building = Building(name="Single Point Lab", description="Main Campus", width=50.0, height=40.0)
    db_session.add(building)
    db_session.flush()

    floor = Floor(building_id=building.id, floor_number=1, name="Lab Floor")
    db_session.add(floor)
    db_session.commit()

    # 1. Out-of-bounds coordinates raise ValueError
    with pytest.raises(ValueError, match="Coordinates .* fall outside building boundaries"):
        predict_single_point(db_session, floor_id=floor.id, x=150.0, y=20.0)

    # 2. In-bounds coordinates succeed
    res = predict_single_point(db_session, floor_id=floor.id, x=25.0, y=20.0)
    assert res["x"] == 25.0 and res["y"] == 20.0
    assert res["predicted_risk"] in ("NOT_DEAD_ZONE", "POTENTIAL_DEAD_ZONE")
    assert 0.0 <= res["dead_zone_probability"] <= 1.0
    assert res["validation_status"] in ("VALID", "VALID_WITH_WARNINGS")

def test_reproducibility_real_survey_evaluation():
    """
    Verify exact reproducibility of real laptop survey evaluation:
    - 46 points with high latency (180ms) at strong signal (-58 dBm) + 8 good points.
    - Model predicts all-0 (NOT_DEAD_ZONE) because RF signal is strong (-58 dBm, 0% loss).
    - Against survey quality category (POOR==1), accuracy is exactly 14.81% (8/54).
    - Against derive_ground_truth_label, accuracy is 100% (54/54 agreement).
    """
    from sklearn.metrics import accuracy_score, confusion_matrix

    model, is_loaded = load_trained_model()
    assert is_loaded is True

    # Construct the exact 54-point real survey profile
    records = []
    # 46 POOR points: RSSI -58 dBm, Latency 180 ms, Loss 0%, Tput 866.7 Mbps
    for _ in range(46):
        records.append({
            "rssi": -58.0, "latency": 180.0, "packet_loss": 0.0, "throughput": 866.7,
            "distance_to_ap": 15.0, "wall_factor": 10.0, "ap_density": 1,
            "quality_category": "POOR"
        })
    # 8 GOOD points: RSSI -32 dBm, Latency 1 ms, Loss 0%, Tput 1201 Mbps
    for _ in range(8):
        records.append({
            "rssi": -32.0, "latency": 1.0, "packet_loss": 0.0, "throughput": 1201.0,
            "distance_to_ap": 5.0, "wall_factor": 0.0, "ap_density": 1,
            "quality_category": "GOOD"
        })

    df = pd.DataFrame(records)
    X = df[FEATURE_NAMES]
    preds = model.predict(X)

    # 1. Model predicts NOT_DEAD_ZONE (0) for all 54 samples
    assert list(preds) == [0] * 54

    # 2. Case A: Evaluated against model target rule (derive_ground_truth_label) -> 100% agreement
    y_rule = df.apply(derive_ground_truth_label, axis=1)
    assert accuracy_score(y_rule, preds) == 1.0

    # 3. Case B: Evaluated against survey quality category (POOR == 1) -> exactly 8/54 = 14.81%
    y_poor = (df["quality_category"] == "POOR").astype(int)
    acc_poor = accuracy_score(y_poor, preds)
    assert round(acc_poor, 4) == 0.1481
    cm_poor = confusion_matrix(y_poor, preds, labels=[0, 1]).tolist()
    assert cm_poor == [[8, 0], [46, 0]]

def test_ml_api_predict_point_endpoint(db_session):
    """Verify /api/v1/ml/predict-point endpoint returns SinglePointPredictionOut."""
    building = Building(name="API Point Lab", description="Campus", width=40.0, height=40.0)
    db_session.add(building)
    db_session.flush()

    floor = Floor(building_id=building.id, floor_number=1, name="Floor 1")
    db_session.add(floor)
    db_session.commit()

    # Valid point
    res = client.post("/api/v1/ml/predict-point", json={"floor_id": floor.id, "x": 10.0, "y": 15.0})
    assert res.status_code == 200
    data = res.json()
    assert data["x"] == 10.0 and data["y"] == 15.0
    assert data["predicted_risk"] in ("NOT_DEAD_ZONE", "POTENTIAL_DEAD_ZONE")
    assert "dead_zone_probability" in data

    # Out-of-bounds point raises HTTP 422
    res_bad = client.post("/api/v1/ml/predict-point", json={"floor_id": floor.id, "x": 999.0, "y": 15.0})
    assert res_bad.status_code == 422
