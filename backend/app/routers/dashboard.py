from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np

from app.database import get_db
from app.models.building import Building, Floor, Room, Wall
from app.models.ap import AccessPoint, APRecommendation
from app.models.measurement import SimulationRun, Measurement
from app.models.dead_zone import DeadZone
from app.models.prediction import PredictionGridPoint, MLModelMetadata
from app.simulation.building_factory import create_default_campus_building
from app.simulation.scenarios import apply_scenario
from app.simulation.rf_engine import RFEngine
from app.dead_zone_engine.detector import detect_dead_zones_for_run
from app.dead_zone_engine.persistence import evaluate_persistence
from app.ml.trainer import train_dead_zone_classifier
from app.ml.predictor import predict_dead_zones_on_grid
from app.optimizer.ap_recommender import recommend_access_points, run_before_after_simulation
from app.routers.dead_zones import parse_dead_zone

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Demo Orchestration"])

@router.post("/demo")
def generate_demo_environment(scenario_name: str = "Laboratory Dead Zone", db: Session = Depends(get_db)):
    """
    ONE-CLICK DEMO PIPELINE:
    1. Loads/creates virtual building & floor
    2. Applies AP scenario (defaults to 'Laboratory Dead Zone')
    3. Simulates realistic measurements with path loss & wall attenuation
    4. Detects spatial dead zones & evaluates severity
    5. Evaluates persistence
    6. Trains / updates Random Forest model with real metrics
    7. Generates ML predicted dead-zone probability grid map
    8. Calculates AP placement recommendations
    9. Prepares Before vs After verification
    """
    # 1. Ensure building exists
    building = create_default_campus_building(db)
    floor = building.floors[0]

    # 2. Apply scenario APs
    apply_scenario(db, floor_id=floor.id, scenario_name=scenario_name)

    # 3. Simulate baseline measurements
    aps = db.query(AccessPoint).filter(AccessPoint.floor_id == floor.id, AccessPoint.is_active == True).all()
    ap_dicts = [{"id": a.id, "x": a.x, "y": a.y, "tx_power_dbm": a.tx_power_dbm} for a in aps]
    walls = db.query(Wall).filter(Wall.floor_id == floor.id).all()
    wall_dicts = [{"x1": w.x1, "y1": w.y1, "x2": w.x2, "y2": w.y2, "attenuation_db": w.attenuation_db} for w in walls]

    sim_run = SimulationRun(
        floor_id=floor.id,
        name=f"Demo Run - {scenario_name}",
        scenario_name=scenario_name,
        total_points=0,
        is_baseline=True
    )
    db.add(sim_run)
    db.flush()

    rf_engine = RFEngine()
    grid_spacing = 2.0
    xs = np.arange(grid_spacing / 2.0, building.width, grid_spacing)
    ys = np.arange(grid_spacing / 2.0, building.height, grid_spacing)

    measurements = []
    for x in xs:
        for y in ys:
            pt = (float(x), float(y))
            res = rf_engine.simulate_point(pt, ap_dicts, wall_dicts, add_noise=True)
            m = Measurement(
                run_id=sim_run.id,
                floor_id=floor.id,
                ap_id=res["ap_id"],
                x=res["x"],
                y=res["y"],
                rssi=res["rssi"],
                latency=res["latency"],
                packet_loss=res["packet_loss"],
                throughput=res["throughput"],
                distance_to_ap=res["distance_to_ap"],
                wall_factor=res["wall_factor"],
                quality_score=res["quality_score"],
                quality_category=res["quality_category"]
            )
            measurements.append(m)

    db.add_all(measurements)
    sim_run.total_points = len(measurements)
    db.commit()

    # 4. Detect dead zones
    dead_zones = detect_dead_zones_for_run(db, run_id=sim_run.id)

    # 5. Check persistence
    evaluate_persistence(db, current_run_id=sim_run.id)

    # 6. Train Random Forest model
    ml_meta = train_dead_zone_classifier(db, floor_id=floor.id)

    # 7. Predict dead zone risk grid with ML
    predictions = predict_dead_zones_on_grid(db, floor_id=floor.id, run_id=sim_run.id, grid_spacing=2.5)

    # 8. Calculate AP recommendations
    recommendations = recommend_access_points(db, floor_id=floor.id, run_id=sim_run.id, max_recommendations=2)

    return {
        "status": "success",
        "message": "Demo environment fully generated and ready for inspection.",
        "floor_id": floor.id,
        "run_id": sim_run.id,
        "scenario": scenario_name,
        "measurements_count": len(measurements),
        "dead_zones_count": len(dead_zones),
        "predicted_points_count": len(predictions),
        "recommended_aps_count": len(recommendations),
        "ml_accuracy": ml_meta.accuracy,
        "ml_f1": ml_meta.f1_score
    }

@router.get("/summary/{floor_id}")
def get_dashboard_summary(floor_id: int, db: Session = Depends(get_db)):
    """Fetch complete statistics for dashboard cards and floorplan overview."""
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        # Auto-create if empty
        building = create_default_campus_building(db)
        floor = building.floors[0]

    floor_area = (floor.building.width * floor.building.height) if floor.building else 4000.0

    # Prioritize latest baseline simulation run so optimization runs do not overwrite dashboard baseline
    baseline_run = (
        db.query(SimulationRun)
        .filter(SimulationRun.floor_id == floor_id, SimulationRun.is_baseline == True)
        .order_by(SimulationRun.id.desc())
        .first()
    )
    latest_run = baseline_run or (
        db.query(SimulationRun)
        .filter(SimulationRun.floor_id == floor_id)
        .order_by(SimulationRun.id.desc())
        .first()
    )


    if not latest_run:
        return {
            "has_data": False,
            "floor_id": floor.id,
            "current_dead_zones": 0,
            "predicted_dead_zones": 0,
            "total_dead_zone_area": 0.0,
            "percentage_affected": 0.0,
            "high_critical_dead_zones": 0,
            "coverage_score": 0.0,
            "avg_rssi": -90.0,
            "avg_latency": 0.0,
            "avg_packet_loss": 0.0,
            "avg_throughput": 0.0,
            "recommended_aps_count": 0,
            "dead_zones": []
        }

    # Measurements stats
    measurements = db.query(Measurement).filter(Measurement.run_id == latest_run.id).all()
    avg_rssi = round(float(np.mean([m.rssi for m in measurements])), 1) if measurements else 0.0
    avg_latency = round(float(np.mean([m.latency for m in measurements])), 1) if measurements else 0.0
    avg_packet_loss = round(float(np.mean([m.packet_loss for m in measurements])), 1) if measurements else 0.0
    avg_throughput = round(float(np.mean([m.throughput for m in measurements])), 1) if measurements else 0.0
    coverage_score = round(float(np.mean([m.quality_score for m in measurements])), 1) if measurements else 0.0

    # Dead zones
    dead_zones = db.query(DeadZone).filter(DeadZone.run_id == latest_run.id).all()
    total_dz_area = round(sum(dz.affected_area for dz in dead_zones), 1)
    pct_affected = round((total_dz_area / floor_area) * 100.0, 1)
    high_crit_count = sum(1 for dz in dead_zones if dz.severity in ("HIGH", "CRITICAL"))

    # Predicted dead zones
    pred_count = (
        db.query(PredictionGridPoint)
        .filter(
            PredictionGridPoint.run_id == latest_run.id,
            PredictionGridPoint.predicted_risk == "POTENTIAL_DEAD_ZONE"
        )
        .count()
    )

    recs_count = (
        db.query(APRecommendation)
        .filter(APRecommendation.run_id == latest_run.id)
        .count()
    )

    return {
        "has_data": True,
        "floor_id": floor.id,
        "run_id": latest_run.id,
        "scenario_name": latest_run.scenario_name,
        "current_dead_zones": len(dead_zones),
        "predicted_dead_zones": pred_count,
        "total_dead_zone_area": total_dz_area,
        "percentage_affected": pct_affected,
        "high_critical_dead_zones": high_crit_count,
        "coverage_score": coverage_score,
        "avg_rssi": avg_rssi,
        "avg_latency": avg_latency,
        "avg_packet_loss": avg_packet_loss,
        "avg_throughput": avg_throughput,
        "recommended_aps_count": recs_count,
        "dead_zones": [parse_dead_zone(d) for d in dead_zones]
    }
