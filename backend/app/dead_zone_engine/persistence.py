import math
from typing import List
from sqlalchemy.orm import Session
from app.models.dead_zone import DeadZone, DeadZoneObservation
from app.models.measurement import SimulationRun
from app.models.alert import Alert
from app.utils.geometry import point_distance

def evaluate_persistence(db: Session, current_run_id: int, distance_threshold: float = 12.0) -> List[DeadZone]:
    """
    Evaluate dead zones across repeated simulation runs to identify recurring dead zones.
    Calculates persistence score and updates persistence flags & alerts.
    """
    current_dzs = db.query(DeadZone).filter(DeadZone.run_id == current_run_id).all()
    if not current_dzs:
        return []

    current_run = db.query(SimulationRun).filter(SimulationRun.id == current_run_id).first()
    if not current_run:
        return current_dzs

    # Find previous runs on this floor
    historical_runs = (
        db.query(SimulationRun)
        .filter(
            SimulationRun.floor_id == current_run.floor_id,
            SimulationRun.id != current_run_id
        )
        .all()
    )

    if not historical_runs:
        # First run, persistence score baseline
        for dz in current_dzs:
            dz.persistence_score = 0.2
            dz.is_persistent = False
        db.commit()
        return current_dzs

    total_prior_runs = len(historical_runs)

    for dz in current_dzs:
        c1 = (dz.center_x, dz.center_y)
        matched_runs_count = 0

        for prev_run in historical_runs:
            prev_dzs = db.query(DeadZone).filter(DeadZone.run_id == prev_run.id).all()
            for pdz in prev_dzs:
                c2 = (pdz.center_x, pdz.center_y)
                dist = point_distance(c1, c2)
                if dist <= distance_threshold:
                    matched_runs_count += 1
                    # Record observation link
                    obs = DeadZoneObservation(
                        dead_zone_id=dz.id,
                        run_id=prev_run.id,
                        similarity_score=round(max(0.0, 1.0 - (dist / distance_threshold)), 2)
                    )
                    db.add(obs)
                    break # Count each previous run at most once

        persistence_score = min(1.0, round((matched_runs_count + 1) / (total_prior_runs + 1), 2))
        dz.persistence_score = persistence_score
        is_persistent = (matched_runs_count >= 1 and persistence_score >= 0.4) or (matched_runs_count >= 2)
        dz.is_persistent = is_persistent

        if is_persistent:
            alert = Alert(
                alert_type="PERSISTENT_DEAD_ZONE",
                severity="HIGH" if dz.severity in ("LOW", "MEDIUM") else "CRITICAL",
                title=f"Persistent Dead Zone: {dz.name}",
                message=(
                    f"Recurring connectivity dead zone verified in {dz.name} across "
                    f"{matched_runs_count + 1} simulation runs with persistence score {int(persistence_score * 100)}%."
                ),
                floor_id=dz.floor_id,
                dead_zone_id=dz.id,
                location_x=dz.center_x,
                location_y=dz.center_y,
                status="ACTIVE"
            )
            db.add(alert)

    db.commit()
    return current_dzs
