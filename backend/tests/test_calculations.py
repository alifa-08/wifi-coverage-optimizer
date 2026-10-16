"""
Unit tests for Wi-Fi coverage optimization mathematical definitions,
metric deltas, status classifications, room-level health analytics,
and Before vs After simulation consistency.
"""

import pytest
from app.optimizer.calculations import (
    calculate_before_after_metrics,
    classify_room_health
)
from app.database import SessionLocal, Base, engine
from app.models.measurement import SimulationRun, Measurement
from app.models.dead_zone import DeadZone
from app.routers.dashboard import generate_demo_environment
from app.optimizer.ap_recommender import run_before_after_simulation

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

# =========================================================================
# 1. Before vs After Comparative Matrix Tests
# =========================================================================

def test_before_after_metrics_positive_improvement():
    """Verify standard improvement scenario with dead zone reduction."""
    res = calculate_before_after_metrics(
        before_count=4,
        after_count=1,
        before_area=450.0,
        after_area=80.0,
        before_good_pct=40.0,
        after_good_pct=85.0,
        before_poor_pct=35.0,
        after_poor_pct=5.0,
        before_avg_rssi=-78.5,
        after_avg_rssi=-64.2,
        before_avg_latency=110.0,
        after_avg_latency=28.0,
        before_avg_loss=12.0,
        after_avg_loss=0.5,
        before_avg_throughput=25.0,
        after_avg_throughput=160.0
    )

    # Dead-zone reductions (positive = improvement)
    assert res["dead_zone_count_reduction"] == 3
    assert res["dead_zone_count_reduction_pct"] == 75.0
    assert not res["is_count_pct_undefined"]
    assert res["dead_zone_area_reduction"] == 370.0
    assert res["dead_zone_area_reduction_pct"] == 82.2
    assert not res["is_area_pct_undefined"]

    # RF Network performance deltas (positive = improvement)
    assert res["rssi_improvement"] == 14.3
    assert res["latency_reduction"] == 82.0
    assert res["packet_loss_reduction"] == 11.5
    assert res["throughput_improvement"] == 135.0

    # Status indicators
    assert res["status"] == "IMPROVED"
    assert res["area_reduction_status"] == "IMPROVED"


def test_before_after_metrics_worsened_case():
    """
    Verify regression/worsening scenario.
    Ensures negative values are NOT clamped to zero and honest negative signs are retained.
    """
    res = calculate_before_after_metrics(
        before_count=1,
        after_count=3,
        before_area=92.0,
        after_area=910.0,
        before_good_pct=80.0,
        after_good_pct=45.0,
        before_poor_pct=10.0,
        after_poor_pct=40.0,
        before_avg_rssi=-57.4,
        after_avg_rssi=-63.49,
        before_avg_latency=25.0,
        after_avg_latency=45.0,
        before_avg_loss=1.0,
        after_avg_loss=4.5,
        before_avg_throughput=180.0,
        after_avg_throughput=110.0
    )

    # Assert genuine negative deltas (not clamped to 0)
    assert res["dead_zone_count_reduction"] == -2
    assert res["dead_zone_count_reduction_pct"] == -200.0
    assert not res["is_count_pct_undefined"]
    assert res["dead_zone_area_reduction"] == -818.0
    assert res["dead_zone_area_reduction_pct"] == -889.1
    assert not res["is_area_pct_undefined"]

    # Network deltas indicate worsening
    assert res["rssi_improvement"] == -6.09
    assert res["latency_reduction"] == -20.0
    assert res["packet_loss_reduction"] == -3.5
    assert res["throughput_improvement"] == -70.0

    # Status indicators reflect worsening honestly
    assert res["status"] == "WORSENED"
    assert res["area_reduction_status"] == "WORSENED"


def test_before_after_metrics_genuine_zero_delta():
    """
    Verify that when baseline is positive and delta is 0,
    the system reports a genuine 0.0% change, NOT an undefined percentage.
    """
    res = calculate_before_after_metrics(
        before_count=2,
        after_count=2,
        before_area=150.0,
        after_area=150.0,
        before_good_pct=60.0,
        after_good_pct=60.0,
        before_poor_pct=20.0,
        after_poor_pct=20.0,
        before_avg_rssi=-70.0,
        after_avg_rssi=-70.0,
        before_avg_latency=50.0,
        after_avg_latency=50.0,
        before_avg_loss=2.0,
        after_avg_loss=2.0,
        before_avg_throughput=100.0,
        after_avg_throughput=100.0
    )

    assert res["dead_zone_count_reduction"] == 0
    assert res["dead_zone_count_reduction_pct"] == 0.0
    assert not res["is_count_pct_undefined"]
    assert res["dead_zone_area_reduction"] == 0.0
    assert res["dead_zone_area_reduction_pct"] == 0.0
    assert not res["is_area_pct_undefined"]
    assert res["status"] == "UNCHANGED"
    assert res["area_reduction_status"] == "UNCHANGED"


def test_before_after_metrics_zero_baseline():
    """
    Verify zero baseline scenarios:
    1. Clean baseline (before=0, after=0): Percentage is undefined, status is ZERO_BASELINE_CLEAN.
    2. Worsened baseline (before=0, after=50): Percentage is undefined, signed absolute difference
       is preserved (-50.0 m²), status is ZERO_BASELINE_WORSENED.
    """
    # Case 1: Clean zero baseline
    res_clean = calculate_before_after_metrics(
        before_count=0,
        after_count=0,
        before_area=0.0,
        after_area=0.0,
        before_good_pct=100.0,
        after_good_pct=100.0,
        before_poor_pct=0.0,
        after_poor_pct=0.0,
        before_avg_rssi=-50.0,
        after_avg_rssi=-50.0,
        before_avg_latency=15.0,
        after_avg_latency=15.0,
        before_avg_loss=0.0,
        after_avg_loss=0.0,
        before_avg_throughput=200.0,
        after_avg_throughput=200.0
    )
    assert res_clean["dead_zone_count_reduction"] == 0
    assert res_clean["is_count_pct_undefined"] is True
    assert res_clean["dead_zone_area_reduction"] == 0.0
    assert res_clean["is_area_pct_undefined"] is True
    assert res_clean["area_reduction_status"] == "ZERO_BASELINE_CLEAN"
    assert res_clean["status"] == "UNCHANGED"

    # Case 2: Worsened from zero baseline (e.g. dead zone formed)
    res_worsened = calculate_before_after_metrics(
        before_count=0,
        after_count=2,
        before_area=0.0,
        after_area=64.0,
        before_good_pct=100.0,
        after_good_pct=70.0,
        before_poor_pct=0.0,
        after_poor_pct=25.0,
        before_avg_rssi=-50.0,
        after_avg_rssi=-78.0,
        before_avg_latency=15.0,
        after_avg_latency=120.0,
        before_avg_loss=0.0,
        after_avg_loss=8.0,
        before_avg_throughput=200.0,
        after_avg_throughput=40.0
    )
    # Signed absolute difference is preserved!
    assert res_worsened["dead_zone_count_reduction"] == -2
    assert res_worsened["is_count_pct_undefined"] is True
    assert res_worsened["dead_zone_area_reduction"] == -64.0
    assert res_worsened["is_area_pct_undefined"] is True
    assert res_worsened["area_reduction_status"] == "ZERO_BASELINE_WORSENED"
    assert res_worsened["status"] == "WORSENED"


# =========================================================================
# 2. Room Health Classification & Boundary Tests
# =========================================================================

def test_room_health_no_data():
    """Verify rooms with zero points return NO_DATA."""
    assert classify_room_health(None, None, None, None, points_count=0) == "NO_DATA"
    assert classify_room_health(-60.0, 20.0, 0.0, 0.0, points_count=0) == "NO_DATA"
    assert classify_room_health(None, 20.0, 0.0, 0.0, points_count=10) == "NO_DATA"


def test_room_health_partially_missing_metrics():
    """
    CRITICAL REQUIREMENT:
    Partially missing metrics must NOT silently become zero or result in OPTIMAL classification.
    """
    # 1. Strong RSSI (-60 dBm), but latency is missing -> CANNOT be OPTIMAL
    res1 = classify_room_health(avg_rssi=-60.0, avg_latency=None, avg_packet_loss=0.5, poor_ratio=0.0, points_count=15)
    assert res1 != "OPTIMAL", "Missing latency falsely produced OPTIMAL!"
    assert res1 == "INCOMPLETE_DATA"

    # 2. Strong RSSI (-60 dBm), but packet loss is missing -> CANNOT be OPTIMAL
    res2 = classify_room_health(avg_rssi=-60.0, avg_latency=18.0, avg_packet_loss=None, poor_ratio=0.0, points_count=15)
    assert res2 != "OPTIMAL", "Missing packet loss falsely produced OPTIMAL!"
    assert res2 == "INCOMPLETE_DATA"

    # 3. Both latency and packet loss missing -> CANNOT be OPTIMAL
    res3 = classify_room_health(avg_rssi=-55.0, avg_latency=None, avg_packet_loss=None, poor_ratio=0.0, points_count=15)
    assert res3 != "OPTIMAL", "Missing both telemetry fields falsely produced OPTIMAL!"
    assert res3 == "INCOMPLETE_DATA"

    # 4. Critical RSSI (-85 dBm), even with missing latency/loss, is still identified as CRITICAL
    res4 = classify_room_health(avg_rssi=-85.0, avg_latency=None, avg_packet_loss=None, poor_ratio=0.0, points_count=15)
    assert res4 == "CRITICAL"


def test_room_health_critical():
    """Verify severe dead-zone thresholds."""
    # Weak RSSI (< -82 dBm)
    assert classify_room_health(avg_rssi=-84.0, avg_latency=50.0, avg_packet_loss=1.0, poor_ratio=10.0, points_count=10) == "CRITICAL"
    # High dead-zone ratio (> 35%)
    assert classify_room_health(avg_rssi=-74.0, avg_latency=50.0, avg_packet_loss=1.0, poor_ratio=40.0, points_count=10) == "CRITICAL"


def test_room_health_degraded():
    """Verify degraded connectivity thresholds."""
    # RSSI in [-82, -75)
    assert classify_room_health(avg_rssi=-77.0, avg_latency=40.0, avg_packet_loss=2.0, poor_ratio=10.0, points_count=10) == "DEGRADED"
    # High latency (> 120 ms)
    assert classify_room_health(avg_rssi=-65.0, avg_latency=130.0, avg_packet_loss=2.0, poor_ratio=0.0, points_count=10) == "DEGRADED"
    # High packet loss (> 10%)
    assert classify_room_health(avg_rssi=-65.0, avg_latency=30.0, avg_packet_loss=12.0, poor_ratio=0.0, points_count=10) == "DEGRADED"
    # Poor ratio (> 15%)
    assert classify_room_health(avg_rssi=-68.0, avg_latency=30.0, avg_packet_loss=1.0, poor_ratio=18.0, points_count=10) == "DEGRADED"


def test_room_health_moderate():
    """Verify moderate connectivity thresholds."""
    # RSSI in [-75, -70)
    assert classify_room_health(avg_rssi=-72.0, avg_latency=40.0, avg_packet_loss=2.0, poor_ratio=0.0, points_count=10) == "MODERATE"
    # Latency in (80, 120]
    assert classify_room_health(avg_rssi=-65.0, avg_latency=95.0, avg_packet_loss=2.0, poor_ratio=0.0, points_count=10) == "MODERATE"
    # Packet loss in (5, 10]
    assert classify_room_health(avg_rssi=-65.0, avg_latency=30.0, avg_packet_loss=7.0, poor_ratio=0.0, points_count=10) == "MODERATE"
    # Poor ratio in (5, 15]
    assert classify_room_health(avg_rssi=-68.0, avg_latency=30.0, avg_packet_loss=1.0, poor_ratio=8.0, points_count=10) == "MODERATE"


def test_room_health_optimal():
    """Verify pristine signals across ALL metrics return OPTIMAL."""
    assert classify_room_health(avg_rssi=-58.0, avg_latency=22.0, avg_packet_loss=0.2, poor_ratio=0.0, points_count=20) == "OPTIMAL"


def test_room_health_boundary_guarantees():
    """
    Rigorously verify requirements:
    1. Weak RSSI (< -75 dBm) must NEVER produce OPTIMAL.
    2. High packet loss (> 5%) must NEVER produce OPTIMAL.
    3. High latency (> 100ms) must NEVER produce OPTIMAL.
    """
    # 1. RSSI sweep below -75 dBm with zero loss and instant latency
    for rssi_val in [-75.1, -78.0, -82.0, -85.0, -92.0]:
        res = classify_room_health(avg_rssi=rssi_val, avg_latency=10.0, avg_packet_loss=0.0, poor_ratio=0.0, points_count=10)
        assert res != "OPTIMAL", f"RSSI {rssi_val} dBm falsely produced OPTIMAL!"
        assert res in ("DEGRADED", "CRITICAL")

    # 2. Packet loss sweep above 5% with strong RSSI (-50 dBm)
    for loss_val in [5.1, 8.0, 12.0, 25.0]:
        res = classify_room_health(avg_rssi=-50.0, avg_latency=15.0, avg_packet_loss=loss_val, poor_ratio=0.0, points_count=10)
        assert res != "OPTIMAL", f"Packet loss {loss_val}% falsely produced OPTIMAL!"
        assert res in ("MODERATE", "DEGRADED", "CRITICAL")

    # 3. Latency sweep above 100ms with strong RSSI (-50 dBm)
    for lat_val in [101.0, 125.0, 200.0]:
        res = classify_room_health(avg_rssi=-50.0, avg_latency=lat_val, avg_packet_loss=0.0, poor_ratio=0.0, points_count=10)
        assert res != "OPTIMAL", f"Latency {lat_val}ms falsely produced OPTIMAL!"
        assert res in ("MODERATE", "DEGRADED", "CRITICAL")


# =========================================================================
# 3. Deterministic Before vs After Database Consistency Test
# =========================================================================

def test_before_after_simulation_consistency_with_database(db_session):
    """
    Verify Before vs After consistency in an isolated test database:
    1. Simulation IDs match the actual baseline and optimized run records.
    2. Passing an already-optimized run ID auto-resolves to baseline, preventing anomalies.
    3. Metrics match actual database measurements and dead zone hulls.
    """
    # 1. Generate baseline demo environment
    demo = generate_demo_environment(scenario_name="Laboratory Dead Zone", db=db_session)
    baseline_run_id = demo["run_id"]
    floor_id = demo["floor_id"]

    # Verify baseline run record in DB
    baseline_run = db_session.query(SimulationRun).filter(SimulationRun.id == baseline_run_id).first()
    assert baseline_run is not None
    assert baseline_run.is_baseline is True

    # Query DB directly for expected baseline dead zones
    expected_before_dzs = db_session.query(DeadZone).filter(DeadZone.run_id == baseline_run_id).all()
    expected_before_count = len(expected_before_dzs)
    expected_before_area = round(float(sum(dz.affected_area for dz in expected_before_dzs)), 1)
    assert expected_before_count >= 1
    assert expected_before_area > 0.0

    # 2. Run Before vs After
    comp1 = run_before_after_simulation(db_session, floor_id=floor_id, baseline_run_id=baseline_run_id)

    # Verify returned IDs match
    assert comp1.baseline_run_id == baseline_run_id
    assert comp1.optimized_run_id != baseline_run_id

    # Verify Before metrics match DB data
    assert comp1.before_dead_zone_count == expected_before_count
    assert comp1.before_dead_zone_area == expected_before_area
    assert comp1.dead_zone_area_reduction > 0.0
    assert comp1.after_dead_zone_area < comp1.before_dead_zone_area
    assert comp1.status == "IMPROVED"

    # Verify optimized run record exists in DB with is_baseline=False
    optimized_run = db_session.query(SimulationRun).filter(SimulationRun.id == comp1.optimized_run_id).first()
    assert optimized_run is not None
    assert optimized_run.is_baseline is False

    # 3. CRITICAL ANOMALY PREVENTION CHECK:
    # Pass the optimized run ID as the baseline_run_id to run_before_after_simulation
    comp2 = run_before_after_simulation(db_session, floor_id=floor_id, baseline_run_id=comp1.optimized_run_id)

    # Automatic guard must have resolved back to the true baseline run!
    assert comp2.baseline_run_id == baseline_run_id
    assert comp2.before_dead_zone_count == expected_before_count
    assert comp2.before_dead_zone_area == expected_before_area
    assert comp2.dead_zone_area_reduction > 0.0
    assert comp2.status == "IMPROVED"
