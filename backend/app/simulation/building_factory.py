from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.building import Building, Floor, Room, Wall
from app.models.ap import AccessPoint

def create_default_campus_building(db: Session) -> Building:
    """Create or return the default campus building with detailed rooms and walls."""
    existing = db.query(Building).first()
    if existing and existing.floors and len(existing.floors[0].walls) > 0:
        return existing

    if existing:
        # Clear incomplete existing building to recreate cleanly
        db.delete(existing)
        db.commit()


    building = Building(
        name="CSE Department Academic Block",
        description="Two-wing academic building housing computer labs, classrooms, seminar halls, and faculty rooms.",
        width=80.0,
        height=50.0
    )
    db.add(building)
    db.flush()

    floor = Floor(
        building_id=building.id,
        floor_number=1,
        name="Floor 1 - Computer Science & Engineering",
        height_meters=3.8
    )
    db.add(floor)
    db.flush()

    # Define rooms
    rooms_data = [
        {"name": "Classroom 101", "room_type": "classroom", "x1": 0.0, "y1": 0.0, "x2": 26.0, "y2": 20.0, "color": "#dbeafe"},
        {"name": "Classroom 102", "room_type": "classroom", "x1": 26.0, "y1": 0.0, "x2": 52.0, "y2": 20.0, "color": "#e0e7ff"},
        {"name": "Seminar Hall 103", "room_type": "meeting_room", "x1": 52.0, "y1": 0.0, "x2": 80.0, "y2": 20.0, "color": "#ede9fe"},
        {"name": "Central Corridor & Lounge", "room_type": "corridor", "x1": 0.0, "y1": 20.0, "x2": 80.0, "y2": 28.0, "color": "#f1f5f9"},
        {"name": "Software Systems Lab 1", "room_type": "laboratory", "x1": 0.0, "y1": 28.0, "x2": 26.0, "y2": 50.0, "color": "#ccfbf1"},
        {"name": "Advanced AI & IoT Lab 2", "room_type": "laboratory", "x1": 26.0, "y1": 28.0, "x2": 54.0, "y2": 50.0, "color": "#fef3c7"},
        {"name": "Faculty & Administrative Offices", "room_type": "office", "x1": 54.0, "y1": 28.0, "x2": 80.0, "y2": 50.0, "color": "#fae8ff"},
    ]

    for r in rooms_data:
        room = Room(floor_id=floor.id, **r)
        db.add(room)

    # Define walls (x1, y1, x2, y2, type, attenuation_db)
    # Outer boundaries (concrete, 14 dB)
    walls_data = [
        # Outer boundary
        (0.0, 0.0, 80.0, 0.0, "concrete", 14.0),
        (80.0, 0.0, 80.0, 50.0, "concrete", 14.0),
        (80.0, 50.0, 0.0, 50.0, "concrete", 14.0),
        (0.0, 50.0, 0.0, 0.0, "concrete", 14.0),

        # Horizontal corridor walls
        (0.0, 20.0, 80.0, 20.0, "brick", 10.0),
        (0.0, 28.0, 80.0, 28.0, "brick", 10.0),

        # Vertical room dividers - North Wing
        (26.0, 0.0, 26.0, 20.0, "brick", 9.0),
        (52.0, 0.0, 52.0, 20.0, "brick", 9.0),

        # Vertical room dividers - South Wing (Labs have heavier concrete / shielding)
        (26.0, 28.0, 26.0, 50.0, "concrete", 15.0),
        (54.0, 28.0, 54.0, 50.0, "concrete", 15.0),
    ]

    for x1, y1, x2, y2, wtype, atten in walls_data:
        wall = Wall(
            floor_id=floor.id,
            x1=x1, y1=y1, x2=x2, y2=y2,
            wall_type=wtype,
            attenuation_db=atten
        )
        db.add(wall)

    # Initial Access Points (Scenario: Laboratory Dead Zone by default)
    # AP-1 is in Classroom 101, AP-2 is in Faculty Offices.
    # AI & IoT Lab 2 (x: 26-54, y: 28-50) is separated by concrete walls and has no AP, creating a realistic dead zone!
    initial_aps = [
        {"name": "AP-North-West", "x": 13.0, "y": 10.0, "tx_power_dbm": 20.0, "channel": 1, "ssid": "Campus-Net-1"},
        {"name": "AP-South-East", "x": 67.0, "y": 38.0, "tx_power_dbm": 20.0, "channel": 11, "ssid": "Campus-Net-2"}
    ]

    for ap_info in initial_aps:
        ap = AccessPoint(floor_id=floor.id, **ap_info)
        db.add(ap)

    db.commit()
    db.refresh(building)
    return building
