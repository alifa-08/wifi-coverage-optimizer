import pytest
from app.dead_zone_engine.severity import evaluate_dead_zone_severity, diagnose_contributing_factors
from app.database import SessionLocal, Base, engine
from app.models.building import Building, Floor, Room
from app.models.measurement import SimulationRun, Measurement
from app.dead_zone_engine.detector import detect_dead_zones_for_run
from app.dead_zone_engine.persistence import evaluate_persistence

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_dead_zone_severity_logic():
    # Critical condition
    crit = evaluate_dead_zone_severity(avg_rssi=-90.0, avg_latency=300.0, avg_packet_loss=35.0, avg_throughput=0.5)
    assert crit == "CRITICAL"

    # Low / Mild degradation
    low = evaluate_dead_zone_severity(avg_rssi=-79.0, avg_latency=125.0, avg_packet_loss=13.0, avg_throughput=4.5)
    assert low in ("LOW", "MEDIUM")

def test_diagnose_contributing_factors():
    factors = diagnose_contributing_factors(
        avg_rssi=-88.0,
        avg_latency=220.0,
        avg_packet_loss=25.0,
        avg_throughput=0.8,
        avg_distance=32.0,
        avg_wall_factor=24.0
    )
    assert len(factors) >= 3
    assert any("wall attenuation" in f for f in factors)
    assert any("distance" in f for f in factors)
    assert any("packet drop" in f for f in factors)

def test_spatial_clustering_dead_zone_detection(test_db):
    # Setup test floor and run
    building = Building(name="Test Hall", width=40.0, height=40.0)
    test_db.add(building)
    test_db.flush()

    floor = Floor(building_id=building.id, floor_number=1, name="Test Floor")
    test_db.add(floor)
    test_db.flush()

    room = Room(floor_id=floor.id, name="Test Lab", room_type="laboratory", x1=0, y1=0, x2=20, y2=20)
    test_db.add(room)
    test_db.flush()

    run = SimulationRun(floor_id=floor.id, name="Test Run", scenario_name="Test")
    test_db.add(run)
    test_db.flush()

    # Add cluster of 5 poor measurements in Test Lab (x: 5-8, y: 5-8)
    for i in range(5):
        m = Measurement(
            run_id=run.id,
            floor_id=floor.id,
            x=5.0 + (i % 3),
            y=5.0 + (i // 3),
            rssi=-85.0,
            latency=180.0,
            packet_loss=22.0,
            throughput=1.5,
            distance_to_ap=28.0,
            wall_factor=15.0,
            quality_score=20.0,
            quality_category="POOR"
        )
        test_db.add(m)
    test_db.commit()

    dead_zones = detect_dead_zones_for_run(test_db, run_id=run.id, eps_distance=5.0, min_samples=3)
    assert len(dead_zones) >= 1
    dz = dead_zones[0]
    assert dz.num_measurements == 5
    assert dz.affected_area > 0.0
    assert dz.severity in ("HIGH", "CRITICAL")
    assert "Test Lab" in dz.name
