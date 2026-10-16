from typing import List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session

from app.models.building import Floor, Wall, Room
from app.models.ap import AccessPoint, APRecommendation
from app.models.measurement import SimulationRun, Measurement
from app.models.dead_zone import DeadZone
from app.simulation.rf_engine import RFEngine
from app.dead_zone_engine.detector import detect_dead_zones_for_run
from app.schemas.optimization import BeforeAfterComparisonOut, APRecommendationOut
from app.schemas.dead_zone import DeadZoneOut
from app.utils.geometry import point_distance
from app.optimizer.calculations import calculate_before_after_metrics
import json

def generate_candidate_ap_positions(
    db: Session,
    floor_id: int,
    dead_zones: List[DeadZone],
    existing_aps: List[AccessPoint],
    min_separation: float = 12.0
) -> List[Tuple[float, float, str]]:
    """
    Generate intelligent candidate AP positions focused specifically on relieving dead zones.
    """
    candidates = []

    # 1. Candidate at the exact center of each detected dead zone
    for dz in dead_zones:
        # Check separation from existing APs
        dz_pt = (dz.center_x, dz.center_y)
        too_close = any(point_distance(dz_pt, (a.x, a.y)) < min_separation for a in existing_aps)
        if not too_close:
            candidates.append((dz.center_x, dz.center_y, f"Direct dead-zone core: {dz.name}"))

    # 2. Candidate in under-served room centroids
    rooms = db.query(Room).filter(Room.floor_id == floor_id).all()
    for r in rooms:
        cx = round((r.x1 + r.x2) / 2.0, 2)
        cy = round((r.y1 + r.y2) / 2.0, 2)
        pt = (cx, cy)
        too_close = any(point_distance(pt, (a.x, a.y)) < min_separation for a in existing_aps)
        if not too_close:
            # Check if this room has a dead zone
            has_dz = any(r.x1 <= dz.center_x <= r.x2 and r.y1 <= dz.center_y <= r.y2 for dz in dead_zones)
            if has_dz:
                candidates.append((cx, cy, f"Room center of affected area: {r.name}"))

    # If no candidates found, pick grid fallback
    if not candidates:
        floor = db.query(Floor).filter(Floor.id == floor_id).first()
        w = floor.building.width if floor and floor.building else 80.0
        h = floor.building.height if floor and floor.building else 50.0
        candidates.append((w / 2.0, h / 2.0, "Central spatial fallback"))

    return candidates

def recommend_access_points(
    db: Session,
    floor_id: int,
    run_id: int,
    max_recommendations: int = 2
) -> List[APRecommendation]:
    """
    Simulate and evaluate candidate AP placements to eliminate dead zones.
    Ranks placements by simulated dead-zone area reduction and coverage gain.
    """
    dead_zones = db.query(DeadZone).filter(DeadZone.run_id == run_id).all()
    existing_aps = db.query(AccessPoint).filter(AccessPoint.floor_id == floor_id, AccessPoint.is_active == True).all()
    walls = db.query(Wall).filter(Wall.floor_id == floor_id).all()

    existing_ap_dicts = [{"id": a.id, "x": a.x, "y": a.y, "tx_power_dbm": a.tx_power_dbm} for a in existing_aps]
    wall_dicts = [{"x1": w.x1, "y1": w.y1, "x2": w.x2, "y2": w.y2, "attenuation_db": w.attenuation_db} for w in walls]

    # Clear previous recommendations for this run
    db.query(APRecommendation).filter(APRecommendation.run_id == run_id).delete()
    db.flush()

    if not dead_zones:
        db.commit()
        return []

    candidates = generate_candidate_ap_positions(db, floor_id, dead_zones, existing_aps)
    rf_engine = RFEngine()

    # Get sample baseline measurements to evaluate improvement
    measurements = db.query(Measurement).filter(Measurement.run_id == run_id).all()
    if not measurements:
        return []

    baseline_poor_count = sum(1 for m in measurements if m.quality_category == "POOR")
    total_area_dz = sum(dz.affected_area for dz in dead_zones)
    total_dz_count = len(dead_zones)

    evaluated_candidates = []

    for cand_x, cand_y, context_reason in candidates:
        candidate_ap = {"id": 999999, "x": cand_x, "y": cand_y, "tx_power_dbm": 20.0}
        simulated_aps = existing_ap_dicts + [candidate_ap]

        poor_converted = 0
        for m in measurements:
            if m.quality_category == "POOR":
                res = rf_engine.simulate_point((m.x, m.y), simulated_aps, wall_dicts, add_noise=False)
                if res["quality_category"] != "POOR":
                    poor_converted += 1

        relieved_ratio = poor_converted / max(baseline_poor_count, 1)
        expected_area_reduction = round(relieved_ratio * total_area_dz, 1)
        expected_dz_count_reduction = int(round(relieved_ratio * total_dz_count))
        coverage_gain_pct = round(relieved_ratio * (baseline_poor_count / max(len(measurements), 1)) * 100.0, 1)

        evaluated_candidates.append({
            "candidate_x": cand_x,
            "candidate_y": cand_y,
            "area_reduction": expected_area_reduction,
            "count_reduction": max(1, expected_dz_count_reduction) if expected_area_reduction > 0 else 0,
            "coverage_gain": coverage_gain_pct,
            "reason": (
                f"Candidate placed at {context_reason}. Simulated to relieve {relieved_ratio*100:.1f}% "
                f"of poor signal points, recovering approx {expected_area_reduction} m² of dead zone."
            )
        })

    # Sort candidates by area reduction descending and enforce spatial diversity
    evaluated_candidates.sort(key=lambda c: (c["area_reduction"], c["coverage_gain"]), reverse=True)
    top_candidates = []
    for cand in evaluated_candidates:
        pt = (cand["candidate_x"], cand["candidate_y"])
        if not any(point_distance(pt, (tc["candidate_x"], tc["candidate_y"])) < 18.0 for tc in top_candidates):
            top_candidates.append(cand)
            if len(top_candidates) >= max_recommendations:
                break

    recs = []

    for priority, cand in enumerate(top_candidates, start=1):
        rec = APRecommendation(
            run_id=run_id,
            floor_id=floor_id,
            candidate_x=cand["candidate_x"],
            candidate_y=cand["candidate_y"],
            tx_power_dbm=20.0,
            priority=priority,
            reason=cand["reason"],
            expected_dead_zone_reduction_area=cand["area_reduction"],
            expected_dead_zone_count_reduction=cand["count_reduction"],
            expected_coverage_gain_pct=cand["coverage_gain"]
        )
        db.add(rec)
        recs.append(rec)

    db.commit()
    return recs

def run_before_after_simulation(
    db: Session,
    floor_id: int,
    baseline_run_id: int
) -> BeforeAfterComparisonOut:
    """
    Execute end-to-end comparative simulation:
    Measures BEFORE state, applies recommended AP(s), simulates AFTER state,
    and calculates verified dead-zone area reduction and count reduction.
    """
    # 1. Fetch baseline run and ensure it is a true baseline run
    baseline_run = db.query(SimulationRun).filter(SimulationRun.id == baseline_run_id).first()
    if not baseline_run:
        raise ValueError(f"Baseline run {baseline_run_id} not found.")

    # Guard: If an optimized run was passed, resolve to the true baseline run for this floor
    if not baseline_run.is_baseline:
        actual_baseline = (
            db.query(SimulationRun)
            .filter(SimulationRun.floor_id == floor_id, SimulationRun.is_baseline == True)
            .order_by(SimulationRun.id.desc())
            .first()
        )
        if actual_baseline:
            baseline_run = actual_baseline
            baseline_run_id = actual_baseline.id

    before_dzs = db.query(DeadZone).filter(DeadZone.run_id == baseline_run_id).all()
    before_measurements = db.query(Measurement).filter(Measurement.run_id == baseline_run_id).all()
    recs = db.query(APRecommendation).filter(APRecommendation.run_id == baseline_run_id).all()

    if not recs:
        # Generate recommendations first if not present
        recs = recommend_access_points(db, floor_id, baseline_run_id)

    # 2. Calculate Before Metrics
    before_count = len(before_dzs)
    before_area = round(float(sum(dz.affected_area for dz in before_dzs)), 1)
    tot_before = max(len(before_measurements), 1)

    before_good_pct = round(sum(1 for m in before_measurements if m.quality_category == "GOOD") / tot_before * 100.0, 1)
    before_poor_pct = round(sum(1 for m in before_measurements if m.quality_category == "POOR") / tot_before * 100.0, 1)

    before_avg_rssi = round(float(np.mean([m.rssi for m in before_measurements])), 2) if before_measurements else -80.0
    before_avg_lat = round(float(np.mean([m.latency for m in before_measurements])), 2) if before_measurements else 150.0
    before_avg_loss = round(float(np.mean([m.packet_loss for m in before_measurements])), 2) if before_measurements else 20.0
    before_avg_tput = round(float(np.mean([m.throughput for m in before_measurements])), 2) if before_measurements else 5.0

    # 3. Create Optimized Run with added Recommended APs
    existing_aps = db.query(AccessPoint).filter(AccessPoint.floor_id == floor_id, AccessPoint.is_active == True).all()
    ap_dicts = [{"id": a.id, "x": a.x, "y": a.y, "tx_power_dbm": a.tx_power_dbm} for a in existing_aps]

    # Add recommendations into temporary simulation AP pool
    added_recs_count = 0
    for rec in recs:
        ap_dicts.append({
            "id": 1000 + rec.id,
            "x": rec.candidate_x,
            "y": rec.candidate_y,
            "tx_power_dbm": rec.tx_power_dbm
        })
        added_recs_count += 1

    walls = db.query(Wall).filter(Wall.floor_id == floor_id).all()
    wall_dicts = [{"x1": w.x1, "y1": w.y1, "x2": w.x2, "y2": w.y2, "attenuation_db": w.attenuation_db} for w in walls]

    optimized_run = SimulationRun(
        floor_id=floor_id,
        name=f"Optimized AP Deployment (+{added_recs_count} APs)",
        scenario_name=f"{baseline_run.scenario_name} + AP Optimization",
        total_points=len(before_measurements),
        is_baseline=False
    )
    db.add(optimized_run)
    db.flush()

    rf_engine = RFEngine()
    after_measurements = []

    for m in before_measurements:
        res = rf_engine.simulate_point((m.x, m.y), ap_dicts, wall_dicts, add_noise=True)
        after_m = Measurement(
            run_id=optimized_run.id,
            floor_id=floor_id,
            ap_id=res["ap_id"],
            x=m.x,
            y=m.y,
            rssi=res["rssi"],
            latency=res["latency"],
            packet_loss=res["packet_loss"],
            throughput=res["throughput"],
            distance_to_ap=res["distance_to_ap"],
            wall_factor=res["wall_factor"],
            quality_score=res["quality_score"],
            quality_category=res["quality_category"]
        )
        db.add(after_m)
        after_measurements.append(after_m)

    db.commit()

    # 4. Detect dead zones on the optimized run
    after_dzs = detect_dead_zones_for_run(db, run_id=optimized_run.id)

    # 5. Compute After Metrics
    after_count = len(after_dzs)
    after_area = round(float(sum(dz.affected_area for dz in after_dzs)), 1)
    tot_after = max(len(after_measurements), 1)

    after_good_pct = round(sum(1 for m in after_measurements if m.quality_category == "GOOD") / tot_after * 100.0, 1)
    after_poor_pct = round(sum(1 for m in after_measurements if m.quality_category == "POOR") / tot_after * 100.0, 1)

    after_avg_rssi = round(float(np.mean([m.rssi for m in after_measurements])), 2) if after_measurements else -80.0
    after_avg_lat = round(float(np.mean([m.latency for m in after_measurements])), 2) if after_measurements else 150.0
    after_avg_loss = round(float(np.mean([m.packet_loss for m in after_measurements])), 2) if after_measurements else 20.0
    after_avg_tput = round(float(np.mean([m.throughput for m in after_measurements])), 2) if after_measurements else 5.0

    # 6. Compute Verified Deltas & Status Flags (no artificial clamping)
    metrics = calculate_before_after_metrics(
        before_count=before_count,
        after_count=after_count,
        before_area=before_area,
        after_area=after_area,
        before_good_pct=before_good_pct,
        after_good_pct=after_good_pct,
        before_poor_pct=before_poor_pct,
        after_poor_pct=after_poor_pct,
        before_avg_rssi=before_avg_rssi,
        after_avg_rssi=after_avg_rssi,
        before_avg_latency=before_avg_lat,
        after_avg_latency=after_avg_lat,
        before_avg_loss=before_avg_loss,
        after_avg_loss=after_avg_loss,
        before_avg_throughput=before_avg_tput,
        after_avg_throughput=after_avg_tput
    )

    # Format dead zone response objects
    def format_dz_out(dz: DeadZone) -> DeadZoneOut:
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

    return BeforeAfterComparisonOut(
        floor_id=floor_id,
        baseline_run_id=baseline_run_id,
        optimized_run_id=optimized_run.id,
        before_dead_zone_count=metrics["before_dead_zone_count"],
        after_dead_zone_count=metrics["after_dead_zone_count"],
        dead_zone_count_reduction=metrics["dead_zone_count_reduction"],
        dead_zone_count_reduction_pct=metrics["dead_zone_count_reduction_pct"],
        before_dead_zone_area=metrics["before_dead_zone_area"],
        after_dead_zone_area=metrics["after_dead_zone_area"],
        dead_zone_area_reduction=metrics["dead_zone_area_reduction"],
        dead_zone_area_reduction_pct=metrics["dead_zone_area_reduction_pct"],
        before_coverage_good_pct=metrics["before_coverage_good_pct"],
        after_coverage_good_pct=metrics["after_coverage_good_pct"],
        before_coverage_poor_pct=metrics["before_coverage_poor_pct"],
        after_coverage_poor_pct=metrics["after_coverage_poor_pct"],
        before_avg_rssi=metrics["before_avg_rssi"],
        after_avg_rssi=metrics["after_avg_rssi"],
        rssi_improvement=metrics["rssi_improvement"],
        before_avg_latency=metrics["before_avg_latency"],
        after_avg_latency=metrics["after_avg_latency"],
        latency_reduction=metrics["latency_reduction"],
        before_avg_packet_loss=metrics["before_avg_packet_loss"],
        after_avg_packet_loss=metrics["after_avg_packet_loss"],
        packet_loss_reduction=metrics["packet_loss_reduction"],
        before_avg_throughput=metrics["before_avg_throughput"],
        after_avg_throughput=metrics["after_avg_throughput"],
        throughput_improvement=metrics["throughput_improvement"],
        status=metrics["status"],
        area_reduction_status=metrics["area_reduction_status"],
        recommended_aps_added=[APRecommendationOut.model_validate(r) for r in recs],
        before_dead_zones=[format_dz_out(dz) for dz in before_dzs],
        after_dead_zones=[format_dz_out(dz) for dz in after_dzs]
    )
