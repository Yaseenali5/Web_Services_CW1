from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..analytics import median_rent_for_region
from ..analytics import affordability_for_region
from ..analytics import affordability_rankings
router = APIRouter()

@router.get("/")
def analytics_root():
    return {"message": "Analytics endpoints"}

@router.get("/regions/{region_id}/median-rent")
def get_median_rent(region_id: int, db: Session = Depends(get_db)):
    median = median_rent_for_region(db, region_id)
    if median is None:
        raise HTTPException(
            status_code=404,
            detail="No rent data available for this region"
        )
    return {
        "region_id": region_id,
        "median_rent": median
    }


@router.get("/regions/{region_id}/affordability")
def get_affordability(region_id: int, db: Session = Depends(get_db)):
    result = affordability_for_region(db, region_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Insufficient data to compute affordability"
        )
    return result


@router.get("/affordability/rankings")
def get_affordability_rankings(db: Session = Depends(get_db)):
    rankings = affordability_rankings(db)
    if not rankings:
        raise HTTPException(
            status_code=404,
            detail="No affordability data available"
        )
    return rankings


