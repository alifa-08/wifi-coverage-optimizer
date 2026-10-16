from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ap import APRecommendation
from app.schemas.optimization import (
    APRecommendationOut, APRecommendationRequest, BeforeAfterComparisonOut
)
from app.optimizer.ap_recommender import recommend_access_points, run_before_after_simulation

router = APIRouter(prefix="/optimizer", tags=["AP Optimization & Verification"])

@router.post("/recommend", response_model=List[APRecommendationOut])
def get_recommendations(req: APRecommendationRequest, db: Session = Depends(get_db)):
    """
    Generate optimal AP placement recommendations targeted specifically
    to eliminate detected or predicted dead zones.
    """
    recs = recommend_access_points(
        db,
        floor_id=req.floor_id,
        run_id=req.run_id,
        max_recommendations=req.max_recommendations or 2
    )
    return recs

@router.get("/recommendations/{run_id}", response_model=List[APRecommendationOut])
def list_recommendations(run_id: int, db: Session = Depends(get_db)):
    return db.query(APRecommendation).filter(APRecommendation.run_id == run_id).all()

@router.post("/before-after", response_model=BeforeAfterComparisonOut)
def compare_before_after(floor_id: int, baseline_run_id: int, db: Session = Depends(get_db)):
    """
    Simulate and verify the impact of recommended AP placements.
    Computes genuine Dead-Zone Area Reduction and Dead-Zone Count Reduction.
    """
    comparison = run_before_after_simulation(
        db,
        floor_id=floor_id,
        baseline_run_id=baseline_run_id
    )
    return comparison
