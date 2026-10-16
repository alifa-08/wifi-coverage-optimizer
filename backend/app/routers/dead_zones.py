import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.dead_zone import DeadZone, DeadZoneObservation
from app.models.measurement import SimulationRun, Measurement
from app.models.building import Floor
from app.schemas.dead_zone import DeadZoneOut, DeadZoneDetectionRequest
from app.dead_zone_engine.detector import detect_dead_zones_for_run
from app.dead_zone_engine.persistence import evaluate_persistence

router = APIRouter(prefix="/dead-zones", tags=["Dead Zone Detection & Analytics"])

def parse_dead_zone(dz: DeadZone) -> DeadZoneOut:
    return DeadZoneOut(
        id=dz.id,
        run_id=dz.run_id,
        floor_id=dz.floor_id,
        name=dz.name,
        center_x=dz.center_x,
        center_y=dz.center_y,
        bounding_box=json.loads(dz.bounding_box),
        polygon_points=json.loads(dz.polygon_points),
        affected_area=dz.affected_area,
        severity=dz.severity,
        num_measurements=dz.num_measurements,
        avg_rssi=dz.avg_rssi,
        avg_latency=dz.avg_latency,
        avg_packet_loss=dz.avg_packet_loss,
        avg_throughput=dz.avg_throughput,
        nearest_ap_id=dz.nearest_ap_id,
        contributing_factors=json.loads(dz.contributing_factors),
        persistence_score=dz.persistence_score,
        is_persistent=dz.is_persistent,
        created_at=dz.created_at
    )

@router.post("/detect", response_model=List[DeadZoneOut])
def detect_dead_zones(req: DeadZoneDetectionRequest, db: Session = Depends(get_db)):
    """
    Execute spatial clustering and dead-zone detection algorithm.
    Groups low-quality measurements, establishes convex hulls, evaluates
    multi-metric severity, and triggers alert if necessary.
    """
    dzs = detect_dead_zones_for_run(
        db,
        run_id=req.run_id,
        min_samples=req.min_samples,
        eps_distance=req.eps_distance,
        rssi_threshold=req.rssi_threshold
    )
    # Automatically evaluate persistence across prior runs
    evaluate_persistence(db, current_run_id=req.run_id)
    return [parse_dead_zone(d) for d in dzs]

@router.get("/run/{run_id}", response_model=List[DeadZoneOut])
def get_dead_zones_for_run(run_id: int, db: Session = Depends(get_db)):
    dzs = db.query(DeadZone).filter(DeadZone.run_id == run_id).all()
    return [parse_dead_zone(d) for d in dzs]

@router.get("/{dead_zone_id}", response_model=DeadZoneOut)
def get_dead_zone_detail(dead_zone_id: int, db: Session = Depends(get_db)):
    dz = db.query(DeadZone).filter(DeadZone.id == dead_zone_id).first()
    if not dz:
        raise HTTPException(status_code=404, detail="Dead zone not found")
    return parse_dead_zone(dz)

@router.get("/analytics/summary/{floor_id}")
def get_dead_zone_analytics_summary(floor_id: int, db: Session = Depends(get_db)):
    """Provide comprehensive statistics for the Dead Zone Analysis page."""
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")

    total_floor_area = (floor.building.width * floor.building.height) if floor.building else 4000.0

    # Prioritize latest baseline simulation run for consistent dead zone analysis
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
            "total_dead_zones": 0,
            "total_dead_zone_area": 0.0,
            "percentage_affected": 0.0,
            "severity_breakdown": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "critical_count": 0,
            "persistent_count": 0,
            "dead_zones": []
        }

    dzs = db.query(DeadZone).filter(DeadZone.run_id == latest_run.id).all()
    total_dz_area = round(sum(dz.affected_area for dz in dzs), 1)
    pct_affected = round((total_dz_area / total_floor_area) * 100.0, 1)

    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for dz in dzs:
        if dz.severity in severity_counts:
            severity_counts[dz.severity] += 1

    persistent_count = sum(1 for dz in dzs if dz.is_persistent)
    critical_count = severity_counts["HIGH"] + severity_counts["CRITICAL"]

    return {
        "has_data": True,
        "latest_run_id": latest_run.id,
        "scenario_name": latest_run.scenario_name,
        "total_dead_zones": len(dzs),
        "total_dead_zone_area": total_dz_area,
        "percentage_affected": pct_affected,
        "severity_breakdown": severity_counts,
        "critical_count": critical_count,
        "persistent_count": persistent_count,
        "dead_zones": [parse_dead_zone(d) for d in dzs]
    }
