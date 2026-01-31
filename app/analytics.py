from sqlalchemy.orm import Session
from . import models

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
