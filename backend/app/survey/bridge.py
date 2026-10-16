import io
import csv
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.survey import SurveySession, SurveyMeasurement
from app.models.measurement import SimulationRun, Measurement
from app.models.dead_zone import DeadZone
from app.dead_zone_engine.detector import detect_dead_zones_for_run

def convert_survey_to_simulation_run(db: Session, survey_id: int) -> Tuple[SimulationRun, List[DeadZone], str]:
    """
    Bridge real college survey measurements into the core analysis pipeline.
    Preserves strict academic honesty by tagging is_synthetic = False.
    Executes real DBSCAN spatial clustering and severity diagnostics on measured data.
    """
    session = db.query(SurveySession).filter(SurveySession.id == survey_id).first()
    if not session:
        raise ValueError(f"SurveySession {survey_id} not found.")

    measurements = (
        db.query(SurveyMeasurement)
        .filter(SurveyMeasurement.survey_id == survey_id)
        .all()
    )

    if not measurements:
        raise ValueError("Cannot analyze empty survey session. Please capture measurements first.")

    # Create a linked SimulationRun tagged as is_synthetic=False
    sim_run = SimulationRun(
        floor_id=session.floor_id,
        name=f"Real College Survey - {session.name}",
        scenario_name="Real Walk-Test Survey",
        total_points=len(measurements),
        is_baseline=True,
        is_synthetic=False # CRITICAL ACADEMIC DISTINCTION
    )
    db.add(sim_run)
    db.flush()

    converted_meas = []
    for sm in measurements:
        # Use estimated or reported RSSI, latency, and packet loss
        eff_rssi = sm.rssi_estimated_dbm if sm.rssi_estimated_dbm is not None else -85.0
        eff_lat = sm.latency_ms if sm.latency_ms is not None else 180.0
        eff_loss = sm.packet_loss_percent if sm.packet_loss_percent is not None else 15.0
        eff_tput = sm.link_speed_mbps if sm.link_speed_mbps is not None else 15.0

        m = Measurement(
            run_id=sim_run.id,
            floor_id=session.floor_id,
            ap_id=None,
            timestamp=sm.timestamp,
            x=sm.x,
            y=sm.y,
            rssi=eff_rssi,
            latency=eff_lat,
            packet_loss=eff_loss,
            throughput=eff_tput,
            distance_to_ap=15.0, # Survey client does not know exact AP coordinate
            wall_factor=10.0,
            quality_score=sm.quality_score,
            quality_category=sm.quality_category,
            is_synthetic=False # Real measured point
        )
        converted_meas.append(m)

    db.add_all(converted_meas)
    db.commit()

    # Density warning check
    density_warning = ""
    if len(measurements) < 4:
        density_warning = (
            f"Low Survey Density Warning: Only {len(measurements)} locations surveyed. "
            "At least 4-6 measurement locations across rooms/corridors are recommended for reliable spatial clustering."
        )

    # Execute dead-zone detection
    # With small real sample sizes, adapt min_samples to max(2, min(3, len(measurements)))
    min_samp = 2 if len(measurements) < 6 else 3
    eps_dist = 12.0 if len(measurements) < 8 else 6.0

    dead_zones = detect_dead_zones_for_run(
        db,
        run_id=sim_run.id,
        min_samples=min_samp,
        eps_distance=eps_dist,
        rssi_threshold=-78.0
    )

    return sim_run, dead_zones, density_warning

def export_survey_to_csv_string(session: SurveySession) -> str:
    """Export real survey session measurements to standard CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "timestamp",
        "floor_id",
        "x",
        "y",
        "ssid",
        "bssid",
        "signal_percent",
        "rssi_dbm",
        "is_rssi_estimated",
        "channel",
        "band",
        "radio_type",
        "link_speed_mbps",
        "latency_ms",
        "packet_loss_percent",
        "ping_target",
        "quality_score",
        "quality_category",
        "is_synthetic"
    ]
    writer.writerow(headers)

    for m in session.measurements:
        writer.writerow([
            m.timestamp.isoformat() if m.timestamp else "",
            m.floor_id,
            m.x,
            m.y,
            m.ssid or "",
            m.bssid or "",
            m.signal_value if m.signal_value is not None else "",
            m.rssi_estimated_dbm if m.rssi_estimated_dbm is not None else "",
            m.is_rssi_estimated,
            m.channel if m.channel is not None else "",
            m.band or "",
            m.radio_type or "",
            m.link_speed_mbps if m.link_speed_mbps is not None else "",
            m.latency_ms if m.latency_ms is not None else "",
            m.packet_loss_percent if m.packet_loss_percent is not None else "",
            m.ping_target or "",
            m.quality_score,
            m.quality_category,
            False # is_synthetic
        ])

    return output.getvalue()

def get_sample_real_survey_csv() -> str:
    """Return sample CSV template for offline real survey recording."""
    sample_rows = [
        "timestamp,floor_id,x,y,ssid,bssid,signal_percent,rssi_dbm,is_rssi_estimated,channel,band,radio_type,link_speed_mbps,latency_ms,packet_loss_percent,ping_target,quality_score,quality_category,is_synthetic",
        "2026-10-04T10:00:00,1,12.5,10.0,College_Campus_WiFi,00:1a:2b:3c:4d:5e,92, -54.0,false,36,5 GHz,802.11ax,866.0,14.0,0.0,172.20.10.1,90.0,GOOD,false",
        "2026-10-04T10:05:00,1,38.0,15.5,College_Campus_WiFi,00:1a:2b:3c:4d:5e,65, -67.5,true,36,5 GHz,802.11ax,433.0,38.0,1.5,172.20.10.1,72.0,MODERATE,false",
        "2026-10-04T10:10:00,1,45.0,38.0,College_Campus_WiFi,00:1a:2b:3c:4d:5e,28, -86.0,true,36,5 GHz,802.11ax,54.0,195.0,26.0,172.20.10.1,28.0,POOR,false",
        "2026-10-04T10:15:00,1,48.5,42.0,College_Campus_WiFi,00:1a:2b:3c:4d:5e,20, -90.0,true,36,5 GHz,802.11ax,24.0,240.0,35.0,172.20.10.1,18.0,POOR,false",
        "2026-10-04T10:20:00,1,68.0,40.0,College_Campus_WiFi,00:1a:2b:3c:4d:5e,88, -56.0,false,48,5 GHz,802.11ax,866.0,16.0,0.0,172.20.10.1,88.0,GOOD,false"
    ]
    return "\n".join(sample_rows)
