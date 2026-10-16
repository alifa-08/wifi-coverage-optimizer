from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.models.building import Floor, Wall, Room
from app.models.ap import AccessPoint
from app.models.prediction import PredictionGridPoint
from app.simulation.rf_engine import RFEngine
from app.ml.model import load_trained_model, FEATURE_NAMES, compute_ap_density
from app.ml.trainer import train_dead_zone_classifier

def validate_telemetry_features(
    features: Dict[str, Any],
    strict: bool = False
) -> Tuple[Dict[str, float], List[str]]:
    """
    Validate telemetry feature inputs against real physical radio and networking bounds.

    If strict=True, raises ValueError on out-of-range, non-finite (NaN, inf), or missing inputs.
    If strict=False, returns bounded values alongside explicit warning messages rather than
    silently disguising anomalies.
    """
    warnings: List[str] = []
    validated: Dict[str, float] = {}

    # 1. RSSI: typically -100 dBm to -15 dBm
    raw_rssi = features.get("rssi")
    if raw_rssi is None or not np.isfinite(raw_rssi):
        msg = f"Non-finite or missing RSSI ({raw_rssi})"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        validated["rssi"] = -95.0
    elif raw_rssi > -10.0 or raw_rssi < -110.0:
        msg = f"Out-of-range RSSI ({raw_rssi} dBm): physical bounds are [-110.0, -10.0]"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        validated["rssi"] = max(-98.0, min(-20.0, float(raw_rssi)))
    else:
        validated["rssi"] = float(raw_rssi)

    # 2. Latency: typically 2 ms to 2000 ms
    raw_lat = features.get("latency")
    if raw_lat is None or not np.isfinite(raw_lat) or raw_lat < 0.0:
        msg = f"Non-finite, missing, or negative latency ({raw_lat})"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        validated["latency"] = 250.0
    elif raw_lat > 3000.0:
        msg = f"Extreme latency ({raw_lat} ms): exceeds operational threshold (3000 ms)"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        validated["latency"] = min(1000.0, float(raw_lat))
    else:
        validated["latency"] = float(raw_lat)

    # 3. Packet loss: 0% to 100%
    raw_loss = features.get("packet_loss")
    if raw_loss is None or not np.isfinite(raw_loss) or raw_loss < 0.0 or raw_loss > 100.0:
        msg = f"Invalid packet loss ({raw_loss}%): must be finite and within [0.0, 100.0]"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        validated["packet_loss"] = 20.0 if (raw_loss is None or not np.isfinite(raw_loss)) else max(0.0, min(100.0, float(raw_loss)))
    else:
        validated["packet_loss"] = float(raw_loss)

    # 4. Throughput: 0.1 Mbps to 10000 Mbps
    raw_tput = features.get("throughput")
    if raw_tput is None or not np.isfinite(raw_tput) or raw_tput <= 0.0:
        msg = f"Invalid throughput ({raw_tput} Mbps): must be positive and finite"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        validated["throughput"] = 1.0
    else:
        validated["throughput"] = float(raw_tput)

    # 5. Distance to AP: >= 0 meters
    raw_dist = features.get("distance_to_ap")
    if raw_dist is None or not np.isfinite(raw_dist) or raw_dist < 0.0:
        msg = f"Invalid distance to AP ({raw_dist} m): must be finite and non-negative"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        validated["distance_to_ap"] = 20.0
    else:
        validated["distance_to_ap"] = float(raw_dist)

    # 6. Wall factor: >= 0 dB
    raw_wall = features.get("wall_factor")
    if raw_wall is None or not np.isfinite(raw_wall) or raw_wall < 0.0:
        msg = f"Invalid wall factor ({raw_wall} dB): must be non-negative"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        validated["wall_factor"] = 0.0
    else:
        validated["wall_factor"] = float(raw_wall)

    # 7. AP density: integer >= 0
    raw_dens = features.get("ap_density")
    if raw_dens is None or not np.isfinite(raw_dens) or raw_dens < 0:
        msg = f"Invalid AP density ({raw_dens}): must be non-negative integer"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
        validated["ap_density"] = 0.0
    else:
        validated["ap_density"] = float(int(raw_dens))

    return validated, warnings

def predict_single_point(
    db: Session,
    floor_id: int,
    x: float,
    y: float,
    custom_features: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Predict dead-zone probability and risk classification for a single physical coordinate.
    Validates physical inputs and reports warnings for anomalous features.
    """
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise ValueError(f"Floor {floor_id} not found.")

    building = floor.building
    width = building.width if building else 80.0
    height = building.height if building else 50.0

    if x < 0.0 or x > width or y < 0.0 or y > height:
        raise ValueError(f"Coordinates ({x}, {y}) fall outside building boundaries [0..{width}, 0..{height}].")

    model, is_loaded = load_trained_model()
    if not is_loaded:
        train_dead_zone_classifier(db, floor_id=floor_id)
        model, _ = load_trained_model()

    warnings: List[str] = []
    if custom_features:
        features_dict, warnings = validate_telemetry_features(custom_features, strict=False)
    else:
        aps = db.query(AccessPoint).filter(AccessPoint.floor_id == floor_id, AccessPoint.is_active == True).all()
        ap_dicts = [{"id": a.id, "x": a.x, "y": a.y, "tx_power_dbm": a.tx_power_dbm} for a in aps]
        walls = db.query(Wall).filter(Wall.floor_id == floor_id).all()
        wall_dicts = [{"x1": w.x1, "y1": w.y1, "x2": w.x2, "y2": w.y2, "attenuation_db": w.attenuation_db} for w in walls]

        rf_engine = RFEngine()
        sim = rf_engine.simulate_point((x, y), ap_dicts, wall_dicts, add_noise=False)
        density = compute_ap_density(x, y, ap_dicts)
        features_dict, warnings = validate_telemetry_features({
            "rssi": sim.get("rssi"),
            "latency": sim.get("latency"),
            "packet_loss": sim.get("packet_loss"),
            "throughput": sim.get("throughput"),
            "distance_to_ap": sim.get("distance_to_ap"),
            "wall_factor": sim.get("wall_factor"),
            "ap_density": density
        }, strict=False)

    df_feats = pd.DataFrame([features_dict])[FEATURE_NAMES]
    pred = int(model.predict(df_feats)[0])
    probs = model.predict_proba(df_feats)[0]

    classes_list = list(model.classes_) if hasattr(model, "classes_") else [0, 1]
    dz_class_idx = classes_list.index(1) if 1 in classes_list else None
    dz_prob = float(probs[dz_class_idx]) if (dz_class_idx is not None and len(probs) > dz_class_idx) else (1.0 if pred == 1 else 0.0)

    risk = "POTENTIAL_DEAD_ZONE" if dz_prob >= 0.50 else "NOT_DEAD_ZONE"

    return {
        "x": round(x, 2),
        "y": round(y, 2),
        "predicted_risk": risk,
        "dead_zone_probability": round(dz_prob, 3),
        "confidence": round(float(np.max(probs)), 3),
        "features_used": features_dict,
        "warnings": warnings,
        "validation_status": "VALID_WITH_WARNINGS" if warnings else "VALID"
    }

def predict_dead_zones_on_grid(
    db: Session,
    floor_id: int,
    run_id: int,
    grid_spacing: float = 2.0
) -> List[PredictionGridPoint]:
    """
    Generate a spatial grid over the floorplan and predict dead zone risk
    and probability for unmeasured or generalized locations using the ML model.
    """
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise ValueError(f"Floor {floor_id} not found.")

    building = floor.building
    width = building.width if building else 80.0
    height = building.height if building else 50.0

    # Ensure model is trained and loaded
    model, is_loaded = load_trained_model()
    if not is_loaded:
        train_dead_zone_classifier(db, floor_id=floor_id)
        model, _ = load_trained_model()

    aps = db.query(AccessPoint).filter(AccessPoint.floor_id == floor_id, AccessPoint.is_active == True).all()
    ap_dicts = [
        {"id": a.id, "x": a.x, "y": a.y, "tx_power_dbm": a.tx_power_dbm}
        for a in aps
    ]

    walls = db.query(Wall).filter(Wall.floor_id == floor_id).all()
    wall_dicts = [
        {"x1": w.x1, "y1": w.y1, "x2": w.x2, "y2": w.y2, "attenuation_db": w.attenuation_db}
        for w in walls
    ]

    rf_engine = RFEngine()

    # Clear previous predictions for this run
    db.query(PredictionGridPoint).filter(PredictionGridPoint.run_id == run_id).delete()
    db.flush()

    # Generate grid coordinates
    xs = np.arange(grid_spacing / 2.0, width, grid_spacing)
    ys = np.arange(grid_spacing / 2.0, height, grid_spacing)

    records = []
    metadata_list = []

    for x in xs:
        for y in ys:
            pt = (float(x), float(y))
            # Simulate physics parameters for this unmeasured point without random measurement noise
            sim = rf_engine.simulate_point(pt, ap_dicts, wall_dicts, add_noise=False)
            density = compute_ap_density(pt[0], pt[1], ap_dicts)

            # -----------------------------------------------------------------
            # Internal Simulation Grid Boundary Guard:
            # During uniform floorplan grid rasterization, points at building
            # edges or behind thick multiple concrete walls may yield unbounded
            # path loss (signal < -100 dBm). These simulation physics points are
            # bounded to standard RF limits (-98 dBm to -20 dBm) to ensure stable
            # heatmap rendering across the floorplan.
            # -----------------------------------------------------------------
            rssi = float(np.nan_to_num(sim.get("rssi", -95.0), nan=-95.0))
            rssi = max(-98.0, min(-20.0, rssi))
            lat = float(np.nan_to_num(sim.get("latency", 150.0), nan=150.0))
            lat = max(4.0, min(1000.0, lat))
            loss = float(np.nan_to_num(sim.get("packet_loss", 20.0), nan=20.0))
            loss = max(0.0, min(100.0, loss))
            tput = float(np.nan_to_num(sim.get("throughput", 5.0), nan=5.0))
            tput = max(0.1, min(1000.0, tput))
            dist = float(np.nan_to_num(sim.get("distance_to_ap", 20.0), nan=20.0))
            dist = max(0.1, min(200.0, dist))
            wall = float(np.nan_to_num(sim.get("wall_factor", 0.0), nan=0.0))
            wall = max(0.0, min(100.0, wall))

            feature_dict = {
                "rssi": rssi,
                "latency": lat,
                "packet_loss": loss,
                "throughput": tput,
                "distance_to_ap": dist,
                "wall_factor": wall,
                "ap_density": density
            }
            records.append(feature_dict)
            metadata_list.append((pt[0], pt[1], sim, feature_dict))

    if not records:
        return []

    df_features = pd.DataFrame(records)[FEATURE_NAMES]
    predictions = model.predict(df_features)
    probabilities = model.predict_proba(df_features)

    # Class 1 corresponds to POTENTIAL_DEAD_ZONE
    classes_list = list(model.classes_) if hasattr(model, "classes_") else [0, 1]
    dead_zone_class_idx = classes_list.index(1) if 1 in classes_list else None

    grid_objects: List[PredictionGridPoint] = []
    for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
        x, y, sim, feats = metadata_list[i]
        if dead_zone_class_idx is not None and len(prob) > dead_zone_class_idx:
            dz_prob = float(prob[dead_zone_class_idx])
        else:
            dz_prob = 1.0 if pred == 1 else 0.0

        risk = "POTENTIAL_DEAD_ZONE" if dz_prob >= 0.50 else "NOT_DEAD_ZONE"
        confidence = float(np.max(prob)) if len(prob) > 0 else 1.0

        pgp = PredictionGridPoint(
            run_id=run_id,
            floor_id=floor_id,
            x=round(x, 2),
            y=round(y, 2),
            predicted_risk=risk,
            dead_zone_probability=round(dz_prob, 3),
            confidence=round(confidence, 3),
            nearest_ap_id=sim.get("ap_id"),
            estimated_rssi=round(feats["rssi"], 2),
            estimated_latency=round(feats["latency"], 2),
            estimated_packet_loss=round(feats["packet_loss"], 2),
            estimated_throughput=round(feats["throughput"], 2),
            distance_to_ap=round(feats["distance_to_ap"], 2),
            wall_factor=round(feats["wall_factor"], 2)
        )
        db.add(pgp)
        grid_objects.append(pgp)

    db.commit()
    return grid_objects
