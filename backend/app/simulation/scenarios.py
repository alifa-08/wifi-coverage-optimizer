from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.ap import AccessPoint
from app.models.building import Floor

SCENARIO_CONFIGS = {
    "Balanced Coverage": [
        {"name": "AP-North-West", "x": 13.0, "y": 10.0, "tx_power_dbm": 20.0, "channel": 1, "ssid": "Campus-Net-1"},
        {"name": "AP-North-East", "x": 66.0, "y": 10.0, "tx_power_dbm": 20.0, "channel": 6, "ssid": "Campus-Net-2"},
        {"name": "AP-South-West", "x": 13.0, "y": 39.0, "tx_power_dbm": 20.0, "channel": 11, "ssid": "Campus-Net-3"},
        {"name": "AP-South-Center", "x": 40.0, "y": 39.0, "tx_power_dbm": 20.0, "channel": 1, "ssid": "Campus-Net-4"},
        {"name": "AP-South-East", "x": 67.0, "y": 39.0, "tx_power_dbm": 20.0, "channel": 6, "ssid": "Campus-Net-5"}
    ],
    "Laboratory Dead Zone": [
        {"name": "AP-North-West", "x": 13.0, "y": 10.0, "tx_power_dbm": 20.0, "channel": 1, "ssid": "Campus-Net-1"},
        {"name": "AP-South-East", "x": 67.0, "y": 38.0, "tx_power_dbm": 20.0, "channel": 11, "ssid": "Campus-Net-2"}
    ],
    "Corridor Dead Zone": [
        {"name": "AP-Deep-Classroom-101", "x": 6.0, "y": 6.0, "tx_power_dbm": 18.0, "channel": 1, "ssid": "Campus-Net-1"},
        {"name": "AP-Deep-Seminar-103", "x": 72.0, "y": 6.0, "tx_power_dbm": 18.0, "channel": 6, "ssid": "Campus-Net-2"},
        {"name": "AP-Deep-Faculty-Offices", "x": 72.0, "y": 44.0, "tx_power_dbm": 18.0, "channel": 11, "ssid": "Campus-Net-3"}
    ],
    "Poor AP Placement": [
        {"name": "AP-East-1", "x": 62.0, "y": 12.0, "tx_power_dbm": 20.0, "channel": 1, "ssid": "Campus-Net-1"},
        {"name": "AP-East-2", "x": 70.0, "y": 35.0, "tx_power_dbm": 20.0, "channel": 6, "ssid": "Campus-Net-2"}
    ]
}

def apply_scenario(db: Session, floor_id: int, scenario_name: str) -> List[AccessPoint]:
    """Replace active APs with scenario AP configuration."""
    if scenario_name not in SCENARIO_CONFIGS:
        scenario_name = "Laboratory Dead Zone"

    # Remove non-recommended APs on this floor
    db.query(AccessPoint).filter(AccessPoint.floor_id == floor_id).delete()
    db.flush()

    new_aps = []
    for ap_spec in SCENARIO_CONFIGS[scenario_name]:
        ap = AccessPoint(floor_id=floor_id, is_active=True, is_recommended=False, **ap_spec)
        db.add(ap)
        new_aps.append(ap)

    db.commit()
    return new_aps
