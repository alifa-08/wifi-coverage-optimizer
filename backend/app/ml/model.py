import os
import joblib
from typing import List, Dict, Any, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from app.config import settings

FEATURE_NAMES = [
    "rssi",
    "latency",
    "packet_loss",
    "throughput",
    "distance_to_ap",
    "wall_factor",
    "ap_density"
]

TARGET_NAME = "dead_zone_risk"

CLASS_LABELS = ["NOT_DEAD_ZONE", "POTENTIAL_DEAD_ZONE"]

def compute_ap_density(x: float, y: float, aps: List[Dict[str, Any]], radius: float = 25.0) -> int:
    """Calculate the number of operational APs within the given radius."""
    count = 0
    for ap in aps:
        dist = np.hypot(x - ap["x"], y - ap["y"])
        if dist <= radius:
            count += 1
    return count

def derive_ground_truth_label(row: Union[pd.Series, Dict[str, Any]]) -> int:
    """
    Derive realistic multi-feature classification target (0 or 1).
    Analytical multi-parameter dead-zone criterion for RF propagation simulation.
    Represents composite physical network degradation (severe attenuation + packet loss / latency expansion).
    Used to generate benchmark ground truth for the Random Forest surrogate model.
    """
    try:
        rssi = float(row.get("rssi", -95.0) if isinstance(row, dict) else row["rssi"])
    except (TypeError, ValueError, KeyError):
        rssi = -95.0

    try:
        lat = float(row.get("latency", 200.0) if isinstance(row, dict) else row["latency"])
    except (TypeError, ValueError, KeyError):
        lat = 200.0

    try:
        loss = float(row.get("packet_loss", 20.0) if isinstance(row, dict) else row["packet_loss"])
    except (TypeError, ValueError, KeyError):
        loss = 20.0

    try:
        tput = float(row.get("throughput", 1.0) if isinstance(row, dict) else row["throughput"])
    except (TypeError, ValueError, KeyError):
        tput = 1.0

    # Handle NaN or infinite values safely
    if np.isnan(rssi) or np.isinf(rssi):
        rssi = -95.0
    if np.isnan(lat) or np.isinf(lat):
        lat = 200.0
    if np.isnan(loss) or np.isinf(loss):
        loss = 20.0
    if np.isnan(tput) or np.isinf(tput):
        tput = 1.0

    # Dead zone condition: composite network degradation
    is_dead = (
        (rssi < -78.0 and (lat > 110.0 or loss > 14.0 or tput < 6.0)) or
        (lat > 160.0 and loss > 18.0) or
        (rssi < -84.0) or
        (loss > 28.0)
    )
    return 1 if is_dead else 0

def load_trained_model() -> Tuple[RandomForestClassifier, bool]:
    """Load persisted Random Forest model from disk."""
    if os.path.exists(settings.MODEL_PATH):
        try:
            model = joblib.load(settings.MODEL_PATH)
            if hasattr(model, "predict"):
                return model, True
        except Exception:
            pass
    return RandomForestClassifier(n_estimators=100, random_state=42), False
