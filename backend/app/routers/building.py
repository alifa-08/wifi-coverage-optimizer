from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.building import Building, Floor, Room, Wall
from app.models.ap import AccessPoint
from app.schemas.building import (
    BuildingOut, FloorOut, RoomOut, WallOut, AccessPointOut,
    AccessPointCreate, RoomCreate, WallCreate
)
from app.simulation.building_factory import create_default_campus_building

router = APIRouter(prefix="/buildings", tags=["Buildings & Floorplans"])

@router.get("/default", response_model=BuildingOut)
def get_or_create_default_building(db: Session = Depends(get_db)):
    """Retrieve or automatically initialize the default academic block."""
    building = create_default_campus_building(db)
    return building

@router.get("", response_model=List[BuildingOut])
@router.get("/", response_model=List[BuildingOut])
def list_buildings(db: Session = Depends(get_db)):

    return db.query(Building).all()

@router.get("/{building_id}/floors", response_model=List[FloorOut])
def get_floors(building_id: int, db: Session = Depends(get_db)):
    floors = db.query(Floor).filter(Floor.building_id == building_id).all()
    return floors

@router.get("/floors/{floor_id}", response_model=FloorOut)
def get_floor(floor_id: int, db: Session = Depends(get_db)):
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    return floor

@router.get("/floors/{floor_id}/aps", response_model=List[AccessPointOut])
def get_floor_aps(floor_id: int, db: Session = Depends(get_db)):
    return db.query(AccessPoint).filter(AccessPoint.floor_id == floor_id).all()

@router.post("/aps", response_model=AccessPointOut)
def create_ap(ap_in: AccessPointCreate, db: Session = Depends(get_db)):
    ap = AccessPoint(**ap_in.model_dump())
    db.add(ap)
    db.commit()
    db.refresh(ap)
    return ap
