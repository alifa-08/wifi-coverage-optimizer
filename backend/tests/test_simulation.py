import pytest
from app.simulation.rf_engine import RFEngine
from app.utils.geometry import segments_intersect, convex_hull_2d, calculate_polygon_area

def test_rf_engine_path_loss_decreases_with_distance():
    engine = RFEngine(noise_std_dev=0.0)
    ap = {"id": 1, "x": 0.0, "y": 0.0, "tx_power_dbm": 20.0}

    # Close point vs distant point
    rssi_close, dist_close, _ = engine.compute_received_power(ap, (2.0, 0.0), [], add_noise=False)
    rssi_far, dist_far, _ = engine.compute_received_power(ap, 20.0, 0.0, [], add_noise=False) if False else engine.compute_received_power(ap, (20.0, 0.0), [], add_noise=False)

    assert dist_close < dist_far
    assert rssi_close > rssi_far, "Signal strength must decrease with distance"

def test_rf_engine_wall_attenuation():
    engine = RFEngine(noise_std_dev=0.0)
    ap = {"id": 1, "x": 0.0, "y": 0.0, "tx_power_dbm": 20.0}
    walls = [{"x1": 5.0, "y1": -5.0, "x2": 5.0, "y2": 5.0, "attenuation_db": 15.0}]

    rssi_los, _, atten_los = engine.compute_received_power(ap, (10.0, 0.0), [], add_noise=False)
    rssi_wall, _, atten_wall = engine.compute_received_power(ap, (10.0, 0.0), walls, add_noise=False)

    assert atten_wall == 15.0
    assert rssi_wall < rssi_los, "Wall must attenuate the signal"

def test_network_metrics_correlation():
    engine = RFEngine()

    # Good RSSI vs Bad RSSI
    lat_g, loss_g, tput_g, score_g, cat_g = engine.calculate_network_metrics(-50.0, add_noise=False)
    lat_p, loss_p, tput_p, score_p, cat_p = engine.calculate_network_metrics(-88.0, add_noise=False)

    assert cat_g == "GOOD"
    assert cat_p == "POOR"
    assert lat_g < lat_p, "Poor RSSI must have higher latency"
    assert loss_g < loss_p, "Poor RSSI must have higher packet loss"
    assert tput_g > tput_p, "Poor RSSI must have lower throughput"
    assert score_g > score_p, "Good RSSI must have higher quality score"

def test_geometry_helpers():
    # Intersection test
    assert segments_intersect((0, 0), (10, 10), (0, 10), (10, 0)) is True
    assert segments_intersect((0, 0), (2, 2), (5, 5), (10, 10)) is False

    # Hull & Area test
    pts = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0), (2.0, 2.0)]
    hull = convex_hull_2d(pts)
    assert len(hull) == 4 # The center point is interior
    area = calculate_polygon_area(hull)
    assert abs(area - 16.0) < 0.01
