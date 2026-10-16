import pytest
from app.database import SessionLocal, Base, engine
from app.routers.dashboard import generate_demo_environment
from app.optimizer.ap_recommender import recommend_access_points, run_before_after_simulation

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_ap_recommendation_and_before_after_verification(test_db):
    # 1. Run demo pipeline to have realistic baseline with dead zones
    demo_res = generate_demo_environment(scenario_name="Laboratory Dead Zone", db=test_db)
    run_id = demo_res["run_id"]
    floor_id = demo_res["floor_id"]

    # 2. Check recommendations
    recs = recommend_access_points(test_db, floor_id=floor_id, run_id=run_id, max_recommendations=2)
    assert len(recs) >= 1
    assert recs[0].expected_dead_zone_reduction_area > 0.0
    assert len(recs[0].reason) > 10

    # 3. Check Before vs After simulation
    comparison = run_before_after_simulation(test_db, floor_id=floor_id, baseline_run_id=run_id)

    assert comparison.dead_zone_area_reduction > 0.0
    assert comparison.after_dead_zone_area < comparison.before_dead_zone_area
    assert comparison.after_coverage_good_pct >= comparison.before_coverage_good_pct
    assert comparison.rssi_improvement >= 0.0
