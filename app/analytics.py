from sqlalchemy.orm import Session
from . import models
from .models import Region

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

    if affordability_index < 0.30:
        classification = "Affordable"
    elif affordability_index <= 0.45:
        classification = "Moderate stress"
    else:
        classification = "High stress"

    return {
        "region": region.name,
        "median_monthly_rent": median_monthly,
        "median_annual_rent": annual_rent,
        "average_income": region.average_income,
        "affordability_index": round(affordability_index, 2),
        "classification": classification
    }

