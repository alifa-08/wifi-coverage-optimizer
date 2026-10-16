import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session

from app.models.measurement import Measurement, SimulationRun
from app.models.dead_zone import DeadZone
from app.models.building import Room
from app.models.alert import Alert
from app.utils.geometry import convex_hull_2d, calculate_polygon_area, compute_bounding_box
from app.dead_zone_engine.severity import evaluate_dead_zone_severity, diagnose_contributing_factors

def identify_room_at_point(x: float, y: float, rooms: List[Room]) -> str:
    """Find which room encloses the coordinate."""
    for r in rooms:
        if r.x1 <= x <= r.x2 and r.y1 <= y <= r.y2:
            return r.name
    return "Corridor / Open Zone"

def detect_dead_zones_for_run(
    db: Session,
    run_id: int,
    eps_distance: float = 6.0,
    min_samples: int = 3,
    rssi_threshold: float = -78.0
) -> List[DeadZone]:
    """
    Dedicated spatial dead-zone detection algorithm.
    Groups poor measurements using DBSCAN spatial clustering,
    constructs convex boundary hulls, calculates affected floor areas,
    evaluates multi-parameter severity, and diagnoses contributing factors.
    """
    # Fetch run and poor measurements
    run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
    if not run:
        raise ValueError(f"SimulationRun {run_id} not found.")

    poor_measurements = (
        db.query(Measurement)
        .filter(
            Measurement.run_id == run_id,
            (Measurement.quality_category == "POOR") | (Measurement.rssi < rssi_threshold)
        )
        .all()
    )

    # Clear previous dead zones for this specific run
    db.query(DeadZone).filter(DeadZone.run_id == run_id).delete()
    db.flush()

    if len(poor_measurements) < min_samples:
        db.commit()
        return []

    coords = np.array([[m.x, m.y] for m in poor_measurements])
    clustering = DBSCAN(eps=eps_distance, min_samples=min_samples).fit(coords)
    labels = clustering.labels_

    rooms = db.query(Room).filter(Room.floor_id == run.floor_id).all()
    created_dead_zones: List[DeadZone] = []

    unique_labels = set(labels)
    cluster_index = 1

    for label in unique_labels:
        if label == -1:
            # -1 is DBSCAN noise / isolated point. Per requirements:
            # "Do NOT classify a single bad measurement as a dead zone."
            continue

        cluster_indices = np.where(labels == label)[0]
        cluster_pts = coords[cluster_indices]
        cluster_measurements = [poor_measurements[i] for i in cluster_indices]

        # Calculate spatial metrics
        center_x = round(float(np.mean(cluster_pts[:, 0])), 2)
        center_y = round(float(np.mean(cluster_pts[:, 1])), 2)

        pt_tuples = [(float(p[0]), float(p[1])) for p in cluster_pts]
        hull_pts = convex_hull_2d(pt_tuples)
        bbox = compute_bounding_box(pt_tuples)

        # Calculate realistic physical affected area (in m^2)
        # Using shoelace formula on convex hull, or cell-based estimate (each point is 2m x 2m = 4m^2)
        geometric_area = calculate_polygon_area(hull_pts)
        cell_area = len(cluster_measurements) * 4.0
        affected_area = round(max(geometric_area, cell_area), 1)

        # Average network parameters
        avg_rssi = round(float(np.mean([m.rssi for m in cluster_measurements])), 2)
        avg_latency = round(float(np.mean([m.latency for m in cluster_measurements])), 2)
        avg_packet_loss = round(float(np.mean([m.packet_loss for m in cluster_measurements])), 2)
        avg_throughput = round(float(np.mean([m.throughput for m in cluster_measurements])), 2)
        avg_distance = round(float(np.mean([m.distance_to_ap for m in cluster_measurements])), 2)
        avg_wall_factor = round(float(np.mean([m.wall_factor for m in cluster_measurements])), 2)

        # Most common nearest AP
        ap_ids = [m.ap_id for m in cluster_measurements if m.ap_id is not None]
        nearest_ap_id = max(set(ap_ids), key=ap_ids.count) if ap_ids else None

        severity = evaluate_dead_zone_severity(
            avg_rssi, avg_latency, avg_packet_loss, avg_throughput
        )

        factors = diagnose_contributing_factors(
            avg_rssi, avg_latency, avg_packet_loss, avg_throughput, avg_distance, avg_wall_factor
        )

        room_name = identify_room_at_point(center_x, center_y, rooms)
        name = f"DZ-{cluster_index}: {room_name}"

        dz = DeadZone(
            run_id=run_id,
            floor_id=run.floor_id,
            name=name,
            center_x=center_x,
            center_y=center_y,
            bounding_box=json.dumps(bbox),
            polygon_points=json.dumps(hull_pts),
            affected_area=affected_area,
            severity=severity,
            num_measurements=len(cluster_measurements),
            avg_rssi=avg_rssi,
            avg_latency=avg_latency,
            avg_packet_loss=avg_packet_loss,
            avg_throughput=avg_throughput,
            nearest_ap_id=nearest_ap_id,
            contributing_factors=json.dumps(factors),
            persistence_score=0.0,
            is_persistent=False
        )
        db.add(dz)
        created_dead_zones.append(dz)
        cluster_index += 1

    db.commit()

    # Generate alerts for High or Critical dead zones
    for dz in created_dead_zones:
        db.refresh(dz)
        if dz.severity in ("HIGH", "CRITICAL"):
            alert = Alert(
                alert_type="SEVERE_DEAD_ZONE",
                severity=dz.severity,
                title=f"Severe Dead Zone Detected in {dz.name}",
                message=(
                    f"Dead zone with {dz.severity} severity covering {dz.affected_area} m² "
                    f"detected. Average RSSI: {dz.avg_rssi} dBm, Latency: {dz.avg_latency} ms, "
                    f"Packet Loss: {dz.avg_packet_loss}%."
                ),
                floor_id=dz.floor_id,
                dead_zone_id=dz.id,
                location_x=dz.center_x,
                location_y=dz.center_y,
                status="ACTIVE"
            )
            db.add(alert)
    db.commit()

    return created_dead_zones
