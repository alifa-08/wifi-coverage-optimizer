import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.survey.collector import (
    parse_netsh_output,
    parse_ping_output,
    evaluate_real_measurement_quality,
)

client = TestClient(app)

MOCK_NETSH_OUTPUT = """
There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi 6 AX201 160MHz
    GUID                   : 4a2f8c5b-3b4e-4f7d-8e9a-1b2c3d4e5f6a
    Physical address       : 2c:6b:f5:12:34:56
    State                  : connected
    SSID                   : Campus_Library_5G
    BSSID                  : 00:14:22:01:23:45
    Network type           : Infrastructure
    Radio type             : 802.11ax
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Connection mode        : Profile
    Channel                : 36
    Receive rate (Mbps)    : 866.7
    Transmit rate (Mbps)   : 866.7
    Signal                 : 84%
    Rssi                   : -58 dBm
    Profile                : Campus_Library_5G
"""

MOCK_NETSH_SIGNAL_ONLY = """
There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Realtek 8821CE Wireless LAN 802.11ac PCI-E NIC
    State                  : connected
    SSID                   : Hosteler_WiFi
    BSSID                  : a0:04:60:aa:bb:cc
    Radio type             : 802.11ac
    Channel                : 6
    Receive rate (Mbps)    : 144.0
    Transmit rate (Mbps)   : 144.0
    Signal                 : 50%
"""

MOCK_PING_OUTPUT = """
Pinging 192.168.1.1 with 32 bytes of data:
Reply from 192.168.1.1: bytes=32 time=4ms TTL=64
Reply from 192.168.1.1: bytes=32 time=6ms TTL=64

Ping statistics for 192.168.1.1:
    Packets: Sent = 2, Received = 2, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 4ms, Maximum = 6ms, Average = 5ms
"""

def test_parse_netsh_output_with_hardware_rssi():
    data = parse_netsh_output(MOCK_NETSH_OUTPUT)
    assert data["connected"] is True
    assert data["ssid"] == "Campus_Library_5G"
    assert data["bssid"] == "00:14:22:01:23:45"
    assert data["channel"] == 36
    assert data["band"] == "5 GHz"
    assert data["radio_type"] == "802.11ax"
    assert data["signal_percent"] == 84.0
    assert data["rssi_dbm"] == -58.0
    assert data["is_rssi_estimated"] is False
    assert data["link_speed_mbps"] == 866.7

def test_parse_netsh_output_with_signal_percentage_only():
    data = parse_netsh_output(MOCK_NETSH_SIGNAL_ONLY)
    assert data["connected"] is True
    assert data["ssid"] == "Hosteler_WiFi"
    assert data["channel"] == 6
    assert data["band"] == "2.4 GHz"
    assert data["signal_percent"] == 50.0
    # Standard Microsoft formula: (50 / 2) - 100 = -75.0 dBm
    assert data["rssi_dbm"] == -75.0
    assert data["is_rssi_estimated"] is True

def test_parse_ping_output():
    ping = parse_ping_output(MOCK_PING_OUTPUT)
    assert ping["latency_ms"] == 5.0
    assert ping["packet_loss_percent"] == 0.0

def test_evaluate_real_measurement_quality():
    # Good signal
    score_good, cat_good = evaluate_real_measurement_quality(signal_percent=85.0, latency_ms=10.0, packet_loss=0.0)
    assert cat_good == "GOOD"
    assert score_good >= 70.0

    # Poor signal & high latency
    score_poor, cat_poor = evaluate_real_measurement_quality(signal_percent=20.0, latency_ms=250.0, packet_loss=40.0)
    assert cat_poor == "POOR"
    assert score_poor < 45.0

def test_survey_endpoints_and_workflow():
    # 1. Check live telemetry endpoint
    res_wifi = client.get("/api/v1/survey/current-wifi")
    assert res_wifi.status_code == 200
    wifi_data = res_wifi.json()
    assert "connected" in wifi_data

    # 2. Check gateway discovery endpoint
    res_gw = client.get("/api/v1/survey/gateway")
    assert res_gw.status_code == 200
    assert "default_gateway" in res_gw.json()

    # 3. Create a new survey session
    session_payload = {
        "name": "Integration Test Academic Survey",
        "building_id": 1,
        "floor_id": 1,
        "ping_target": "127.0.0.1",
        "floorplan_width_m": 80.0,
        "floorplan_height_m": 50.0,
        "notes": "Testing real survey flow"
    }
    res_sess = client.post("/api/v1/survey/sessions", json=session_payload)
    assert res_sess.status_code == 200
    session_data = res_sess.json()
    assert session_data["name"] == "Integration Test Academic Survey"
    session_id = session_data["id"]

    # 4. Capture measurements with mocked Windows network output
    with patch("app.survey.collector.subprocess.run") as mock_sub:
        mock_sub.return_value.stdout = MOCK_NETSH_OUTPUT
        mock_sub.return_value.returncode = 0

        # Capture Point 1: Good region
        meas1 = client.post(
            f"/api/v1/survey/sessions/{session_id}/capture",
            json={"x": 15.0, "y": 20.0, "notes": "Near AP"}
        )
        assert meas1.status_code == 200
        m1_data = meas1.json()
        assert m1_data["is_synthetic"] is False
        assert m1_data["x"] == 15.0
        assert m1_data["y"] == 20.0
        assert m1_data["measurement_source"] == "windows_netsh_survey"

        # Capture Point 2: Far corner
        meas2 = client.post(
            f"/api/v1/survey/sessions/{session_id}/capture",
            json={"x": 72.0, "y": 42.0, "notes": "Far lab corner"}
        )
        assert meas2.status_code == 200
        m2_data = meas2.json()
        assert m2_data["x"] == 72.0

    # 5. Export Survey to CSV
    res_csv = client.get(f"/api/v1/survey/sessions/{session_id}/export-csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    csv_text = res_csv.text
    assert "timestamp,floor_id,x,y,ssid,bssid,signal_percent,rssi_dbm,is_rssi_estimated" in csv_text
    assert "is_synthetic" in csv_text
    assert "False" in csv_text

    # 6. Sample CSV template download
    res_sample = client.get("/api/v1/survey/sample-csv")
    assert res_sample.status_code == 200
    assert "College_Campus_WiFi" in res_sample.text
    assert "172.20.10.1" in res_sample.text

    # 7. Analyze Survey Session (bridges to dead-zone detection)
    res_analyze = client.post(f"/api/v1/survey/sessions/{session_id}/analyze")
    assert res_analyze.status_code == 200
    analysis = res_analyze.json()
    assert analysis["survey_id"] == session_id
    assert analysis["total_survey_points"] == 2
    assert "density_warning" in analysis
    assert "quality_breakdown" in analysis
