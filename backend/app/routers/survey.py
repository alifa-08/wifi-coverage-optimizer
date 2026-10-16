import io
import csv
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.survey import SurveySession, SurveyMeasurement
from app.models.building import Floor, Building
from app.schemas.survey import (
    LiveWifiStatusOut,
    SurveySessionCreate,
    SurveySessionOut,
    SurveyMeasurementCreate,
    SurveyMeasurementOut,
    SurveyAnalysisOut,
)
from app.survey.collector import (
    get_windows_wifi_info,
    measure_network_latency,
    get_default_gateway,
    evaluate_real_measurement_quality,
)
from app.survey.bridge import (
    convert_survey_to_simulation_run,
    export_survey_to_csv_string,
    get_sample_real_survey_csv,
)
from app.routers.dead_zones import parse_dead_zone

router = APIRouter(prefix="/survey", tags=["Real College Survey Mode"])

@router.get("/current-wifi", response_model=LiveWifiStatusOut)
def get_live_wifi_telemetry(target_ip: Optional[str] = "auto"):
    """
    Query real Windows Wi-Fi adapter telemetry and execute a live ping test
    against the local gateway. No data is stored.
    """
    wifi = get_windows_wifi_info()
    ping = measure_network_latency(target=target_ip, count=2)

    return LiveWifiStatusOut(
        connected=wifi["connected"],
        state=wifi.get("state"),
        ssid=wifi.get("ssid"),
        bssid=wifi.get("bssid"),
        signal_percent=wifi.get("signal_percent"),
        signal_unit=wifi.get("signal_unit", "%"),
        rssi_dbm=wifi.get("rssi_dbm"),
        is_rssi_estimated=wifi.get("is_rssi_estimated", True),
        channel=wifi.get("channel"),
        band=wifi.get("band"),
        radio_type=wifi.get("radio_type"),
        link_speed_mbps=wifi.get("link_speed_mbps"),
        latency_ms=ping.get("latency_ms"),
        packet_loss_percent=ping.get("packet_loss_percent"),
        ping_target=ping.get("target"),
        ping_target_type=ping.get("target_type"),
        error=wifi.get("error")
    )

@router.get("/gateway")
def get_gateway_ip():
    """Retrieve auto-detected default gateway IP address."""
    gw = get_default_gateway()
    return {"default_gateway": gw or "127.0.0.1", "detected": gw is not None}

@router.post("/sessions", response_model=SurveySessionOut)
def create_survey_session(session_in: SurveySessionCreate, db: Session = Depends(get_db)):
    """Create a new Real College Survey session."""
    floor = db.query(Floor).filter(Floor.id == session_in.floor_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")

    session = SurveySession(
        name=session_in.name,
        building_id=session_in.building_id,
        floor_id=session_in.floor_id,
        ping_target=session_in.ping_target or "auto",
        floorplan_width_m=session_in.floorplan_width_m or 80.0,
        floorplan_height_m=session_in.floorplan_height_m or 50.0,
        notes=session_in.notes
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[SurveySessionOut])
def list_survey_sessions(floor_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(SurveySession).order_by(SurveySession.id.desc())
    if floor_id:
        query = query.filter(SurveySession.floor_id == floor_id)
    return query.all()

@router.get("/sessions/{session_id}", response_model=SurveySessionOut)
def get_survey_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SurveySession).filter(SurveySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Survey session not found")
    return session

@router.post("/sessions/{session_id}/capture", response_model=SurveyMeasurementOut)
def capture_survey_measurement(
    session_id: int,
    req: SurveyMeasurementCreate,
    db: Session = Depends(get_db)
):
    """
    Capture live Windows Wi-Fi telemetry and local ping metrics tagged with the selected floorplan coordinate.
    Strictly preserves is_synthetic = False.
    """
    session = db.query(SurveySession).filter(SurveySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Survey session not found")

    # 1. Query Wi-Fi card
    wifi = get_windows_wifi_info()

    # 2. Ping local gateway / target
    target_to_use = req.target_ip if req.target_ip != "auto" else session.ping_target
    ping = measure_network_latency(target=target_to_use, count=2)

    # 3. Categorize quality
    q_score, q_cat = evaluate_real_measurement_quality(
        signal_pct=wifi.get("signal_percent"),
        rssi_dbm=wifi.get("rssi_dbm"),
        latency_ms=ping.get("latency_ms"),
        packet_loss_pct=ping.get("packet_loss_percent")
    )

    measurement = SurveyMeasurement(
        survey_id=session.id,
        building_id=session.building_id,
        floor_id=session.floor_id,
        x=req.x,
        y=req.y,
        timestamp=datetime.utcnow(),
        ssid=wifi.get("ssid"),
        bssid=wifi.get("bssid"),
        signal_value=wifi.get("signal_percent"),
        signal_unit="%",
        rssi_estimated_dbm=wifi.get("rssi_dbm"),
        is_rssi_estimated=wifi.get("is_rssi_estimated", True),
        channel=wifi.get("channel"),
        band=wifi.get("band"),
        radio_type=wifi.get("radio_type"),
        link_speed_mbps=wifi.get("link_speed_mbps"),
        latency_ms=ping.get("latency_ms"),
        packet_loss_percent=ping.get("packet_loss_percent"),
        ping_target=ping.get("target"),
        ping_target_type=ping.get("target_type", "local_gateway"),
        quality_score=q_score,
        quality_category=q_cat,
        is_synthetic=False, # REAL MEASUREMENT
        measurement_source="windows_netsh_survey",
        notes=req.notes
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)

    return measurement

@router.delete("/sessions/{session_id}/measurements")
def clear_survey_measurements(session_id: int, db: Session = Depends(get_db)):
    """Clear all measurements in a survey session."""
    session = db.query(SurveySession).filter(SurveySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Survey session not found")
    db.query(SurveyMeasurement).filter(SurveyMeasurement.survey_id == session_id).delete()
    db.commit()
    return {"message": "Survey measurements cleared successfully."}

@router.post("/sessions/{session_id}/analyze", response_model=SurveyAnalysisOut)
def analyze_real_survey(session_id: int, db: Session = Depends(get_db)):
    """
    Execute spatial dead-zone detection directly on real survey measurements.
    Converts measurements with is_synthetic=False tag and runs DBSCAN clustering.
    """
    session = db.query(SurveySession).filter(SurveySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Survey session not found")

    try:
        sim_run, dead_zones, density_warn = convert_survey_to_simulation_run(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    measurements = session.measurements
    rssis = [m.rssi_estimated_dbm for m in measurements if m.rssi_estimated_dbm is not None]
    lats = [m.latency_ms for m in measurements if m.latency_ms is not None]
    losses = [m.packet_loss_percent for m in measurements if m.packet_loss_percent is not None]

    avg_rssi = round(sum(rssis) / len(rssis), 1) if rssis else -85.0
    avg_lat = round(sum(lats) / len(lats), 1) if lats else 150.0
    avg_loss = round(sum(losses) / len(losses), 1) if losses else 20.0

    breakdown = {
        "GOOD": sum(1 for m in measurements if m.quality_category == "GOOD"),
        "MODERATE": sum(1 for m in measurements if m.quality_category == "MODERATE"),
        "POOR": sum(1 for m in measurements if m.quality_category == "POOR"),
    }

    return SurveyAnalysisOut(
        survey_id=session.id,
        linked_simulation_run_id=sim_run.id,
        total_survey_points=len(measurements),
        dead_zones=[parse_dead_zone(dz) for dz in dead_zones],
        density_warning=density_warn or None,
        average_rssi_dbm=avg_rssi,
        average_latency_ms=avg_lat,
        average_packet_loss_pct=avg_loss,
        quality_breakdown=breakdown
    )

@router.get("/sessions/{session_id}/export-csv")
def export_survey_csv(session_id: int, db: Session = Depends(get_db)):
    """Export real survey measurements as a downloadable CSV file."""
    session = db.query(SurveySession).filter(SurveySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Survey session not found")

    csv_text = export_survey_to_csv_string(session)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=real_survey_{session_id}.csv"}
    )

@router.get("/sample-csv")
def download_sample_survey_csv():
    """Download a template CSV format for offline real survey recording."""
    csv_text = get_sample_real_survey_csv()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_real_survey_template.csv"}
    )
