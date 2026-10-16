import numpy as np
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.building import Floor, Wall
from app.models.ap import AccessPoint
from app.models.measurement import SimulationRun, Measurement
from app.schemas.simulation import SimulationRunOut, MeasurementOut, SimulationRunRequest
from app.simulation.rf_engine import RFEngine
from app.simulation.scenarios import apply_scenario, SCENARIO_CONFIGS

router = APIRouter(prefix="/simulation", tags=["Simulation"])

@router.get("/scenarios", response_model=List[str])
def list_available_scenarios():
    """List available predefined simulation scenarios."""
    return list(SCENARIO_CONFIGS.keys())

@router.post("/scenario/apply")
def apply_simulation_scenario(floor_id: int, scenario_name: str, db: Session = Depends(get_db)):
    """Apply a predefined scenario configuration to the floor."""
    aps = apply_scenario(db, floor_id=floor_id, scenario_name=scenario_name)
    return {"message": f"Applied scenario '{scenario_name}'", "active_ap_count": len(aps)}

@router.post("/run", response_model=SimulationRunOut)
def run_simulation(req: SimulationRunRequest, db: Session = Depends(get_db)):
    """
    Execute a physics-based Wi-Fi simulation run on the floorplan.
    Generates realistic spatial measurements with path loss, wall attenuation, and noise.
    """
    floor = db.query(Floor).filter(Floor.id == req.floor_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")

    building = floor.building
    width = building.width if building else 80.0
    height = building.height if building else 50.0

    aps = db.query(AccessPoint).filter(AccessPoint.floor_id == req.floor_id, AccessPoint.is_active == True).all()
    ap_dicts = [{"id": a.id, "x": a.x, "y": a.y, "tx_power_dbm": a.tx_power_dbm} for a in aps]

    walls = db.query(Wall).filter(Wall.floor_id == req.floor_id).all()
    wall_dicts = [{"x1": w.x1, "y1": w.y1, "x2": w.x2, "y2": w.y2, "attenuation_db": w.attenuation_db} for w in walls]

    sim_run = SimulationRun(
        floor_id=req.floor_id,
        name=f"Run - {req.scenario_name}",
        scenario_name=req.scenario_name or "Standard",
        total_points=0,
        is_baseline=True
    )
    db.add(sim_run)
    db.flush()

    rf_engine = RFEngine()
    xs = np.arange(req.grid_spacing / 2.0, width, req.grid_spacing)
    ys = np.arange(req.grid_spacing / 2.0, height, req.grid_spacing)

    measurement_objects = []
    for x in xs:
        for y in ys:
            pt = (float(x), float(y))
            res = rf_engine.simulate_point(pt, ap_dicts, wall_dicts, add_noise=req.include_noise)
            m = Measurement(
                run_id=sim_run.id,
                floor_id=req.floor_id,
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
            measurement_objects.append(m)

    if req.save_to_db:
        db.add_all(measurement_objects)
        sim_run.total_points = len(measurement_objects)
        db.commit()
        db.refresh(sim_run)

    return sim_run

@router.get("/runs/{floor_id}", response_model=List[SimulationRunOut])
def get_simulation_runs(floor_id: int, db: Session = Depends(get_db)):
    return db.query(SimulationRun).filter(SimulationRun.floor_id == floor_id).order_by(SimulationRun.id.desc()).all()

@router.get("/runs/{run_id}/measurements", response_model=List[MeasurementOut])
def get_run_measurements(run_id: int, db: Session = Depends(get_db)):
    return db.query(Measurement).filter(Measurement.run_id == run_id).all()
