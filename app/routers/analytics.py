from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import schemas
from ..database import get_db
from ..analytics import median_rent_for_region
from ..analytics import affordability_for_region
from ..analytics import affordability_rankings
from ..analytics import affordability_simulation_for_region
router = APIRouter()

@router.get("/", response_model=schemas.AnalyticsRootResponse)
def analytics_root():
    return {"message": "Analytics endpoints"}

@router.get("/regions/{region_id}/median-rent", response_model=schemas.MedianRentResponse)
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


@router.get("/regions/{region_id}/affordability", response_model=schemas.AffordabilityResult)
def get_affordability(region_id: int, db: Session = Depends(get_db)):
    result = affordability_for_region(db, region_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Insufficient data to compute affordability"
        )
    return result


@router.get("/regions/{region_id}/affordability/simulate", response_model=schemas.AffordabilitySimulationResponse)
def simulate_affordability(
    region_id: int,
    monthly_rent: Optional[float] = Query(default=None, gt=0),
    average_income: Optional[float] = Query(default=None, gt=0),
    rent_change_pct: float = Query(default=0.0, ge=-100, le=1000),
    income_change_pct: float = Query(default=0.0, ge=-100, le=1000),
    db: Session = Depends(get_db),
):
    result = affordability_simulation_for_region(
        db=db,
        region_id=region_id,
        monthly_rent=monthly_rent,
        average_income=average_income,
        rent_change_pct=rent_change_pct,
        income_change_pct=income_change_pct,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Insufficient data to compute affordability simulation",
        )
    return result


@router.get("/affordability/rankings", response_model=list[schemas.AffordabilityResult])
def get_affordability_rankings(db: Session = Depends(get_db)):
    rankings = affordability_rankings(db)
    if not rankings:
        raise HTTPException(
            status_code=404,
            detail="No affordability data available"
        )
    return rankings
