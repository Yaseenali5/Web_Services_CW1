from sqlalchemy.orm import Session
from . import models
from .models import Region
from typing import Optional


def _classify_affordability(affordability_index: float) -> str:
    if affordability_index < 0.30:
        return "Affordable"
    if affordability_index <= 0.45:
        return "Moderate stress"
    return "High stress"

def median_rent_for_region(db: Session, region_id: int):
    rents = (
        db.query(models.Listing.price)
        .filter(
            models.Listing.region_id == region_id,
            models.Listing.listing_type == "rent"
        )
        .all()
    )

    if not rents:
        return None

    prices = sorted([r[0] for r in rents])
    n = len(prices)

    if n % 2 == 1:
        return prices[n // 2]
    else:
        return (prices[n // 2 - 1] + prices[n // 2]) / 2

def affordability_for_region(db: Session, region_id: int):
    median_monthly = median_rent_for_region(db, region_id)
    if median_monthly is None:
        return None

    region = db.query(Region).filter(Region.id == region_id).first()
    if not region or not region.average_income:
        return None

    annual_rent = median_monthly * 12
    affordability_index = annual_rent / region.average_income

    classification = _classify_affordability(affordability_index)

    return {
        "region": region.name,
        "median_monthly_rent": median_monthly,
        "median_annual_rent": annual_rent,
        "average_income": region.average_income,
        "affordability_index": round(affordability_index, 2),
        "classification": classification
    }


def affordability_simulation_for_region(
    db: Session,
    region_id: int,
    monthly_rent: Optional[float] = None,
    average_income: Optional[float] = None,
    rent_change_pct: float = 0.0,
    income_change_pct: float = 0.0,
):
    """Run a what-if affordability simulation for a region."""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        return None

    baseline_rent = median_rent_for_region(db, region_id)
    if baseline_rent is None:
        return None
    if not region.average_income:
        return None

    simulated_rent = monthly_rent if monthly_rent is not None else baseline_rent
    simulated_income = average_income if average_income is not None else region.average_income

    simulated_rent = simulated_rent * (1 + rent_change_pct / 100)
    simulated_income = simulated_income * (1 + income_change_pct / 100)

    if simulated_income <= 0:
        return None

    baseline_index = (baseline_rent * 12) / region.average_income
    simulated_index = (simulated_rent * 12) / simulated_income

    return {
        "region": region.name,
        "baseline": {
            "median_monthly_rent": round(baseline_rent, 2),
            "average_income": round(region.average_income, 2),
            "affordability_index": round(baseline_index, 2),
            "classification": _classify_affordability(baseline_index),
        },
        "scenario": {
            "monthly_rent": round(simulated_rent, 2),
            "average_income": round(simulated_income, 2),
            "rent_change_pct": round(rent_change_pct, 2),
            "income_change_pct": round(income_change_pct, 2),
            "affordability_index": round(simulated_index, 2),
            "classification": _classify_affordability(simulated_index),
        },
        "delta": {
            "index_change": round(simulated_index - baseline_index, 2),
            "classification_changed": _classify_affordability(baseline_index) != _classify_affordability(simulated_index),
        },
    }

def affordability_rankings(db: Session):
    regions = db.query(models.Region).all()
    rankings = []

    for region in regions:
        result = affordability_for_region(db, region.id)
        if result:
            rankings.append(result)

    # sort by affordability_index (lower = more affordable)
    rankings.sort(key=lambda x: x["affordability_index"])
    return rankings

