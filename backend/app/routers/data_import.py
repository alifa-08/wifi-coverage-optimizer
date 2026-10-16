import io
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.building import Floor
from app.models.measurement import SimulationRun, Measurement
from app.dead_zone_engine.detector import detect_dead_zones_for_run

router = APIRouter(prefix="/import", tags=["Data Import"])

@router.post("/csv")
async def import_csv_measurements(
    file: UploadFile = File(...),
    floor_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Import Wi-Fi survey measurements from CSV file.
    Expected columns: timestamp, floor, x, y, rssi, latency, packet_loss, throughput, ap_id
    """
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    required_cols = ["x", "y", "rssi", "latency", "packet_loss", "throughput"]
    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required column '{col}'. Expected: timestamp, floor, x, y, rssi, latency, packet_loss, throughput, ap_id"
            )

    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Target floor not found.")

    sim_run = SimulationRun(
        floor_id=floor_id,
        name=f"CSV Import - {file.filename}",
        scenario_name="Field Survey Data",
        total_points=len(df),
        is_baseline=True
    )
    db.add(sim_run)
    db.flush()

    measurements = []
    for _, row in df.iterrows():
        rssi = float(row["rssi"])
        lat = float(row["latency"])
        loss = float(row["packet_loss"])
        tput = float(row["throughput"])

        # Calculate composite quality score
        if rssi >= -65.0:
            q_score = 85.0
            category = "GOOD"
        elif rssi >= -78.0:
            q_score = 65.0
            category = "MODERATE"
        else:
            q_score = 25.0
            category = "POOR"

        ap_id = int(row["ap_id"]) if "ap_id" in row and pd.notnull(row["ap_id"]) else None

        m = Measurement(
            run_id=sim_run.id,
            floor_id=floor_id,
            ap_id=ap_id,
            x=float(row["x"]),
            y=float(row["y"]),
            rssi=rssi,
            latency=lat,
            packet_loss=loss,
            throughput=tput,
            distance_to_ap=float(row.get("distance_to_ap", 10.0)),
            wall_factor=float(row.get("wall_factor", 0.0)),
            quality_score=q_score,
            quality_category=category
        )
        measurements.append(m)

    db.add_all(measurements)
    db.commit()

    # Automatically run dead-zone detection on the imported data
    detected = detect_dead_zones_for_run(db, run_id=sim_run.id)

    return {
        "message": f"Successfully imported {len(measurements)} measurements from CSV.",
        "run_id": sim_run.id,
        "dead_zones_detected": len(detected)
    }
