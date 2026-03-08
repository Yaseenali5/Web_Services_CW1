from sqlalchemy.orm import Session
from . import models, schemas

def create_region(db: Session, region: schemas.RegionCreate):
    db_region = models.Region(
        name=region.name,
        ons_code=region.ons_code,
        average_income=region.average_income
    )
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region

def get_regions(db: Session):
    return db.query(models.Region).all()

def get_region(db: Session, region_id: int):
    return db.query(models.Region).filter(models.Region.id == region_id).first()

def delete_region(db: Session, region_id: int):
    region = get_region(db, region_id)
    if region:
        db.delete(region)
        db.commit()
    return region

def update_region(db: Session, region_id: int, region_data: schemas.RegionUpdate):
    region = get_region(db, region_id)
    if not region:
        return None

    region.name = region_data.name
    region.ons_code = region_data.ons_code
    region.average_income = region_data.average_income

    db.commit()
    db.refresh(region)
    return region

def create_listing(db: Session, listing: schemas.ListingCreate):
    db_listing = models.Listing(
        region_id=listing.region_id,
        price=listing.price,
        bedrooms=listing.bedrooms,
        listing_type=listing.listing_type
    )
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing

def get_listings(db: Session):
    return db.query(models.Listing).all()

def get_listing(db: Session, listing_id: int):
    return db.query(models.Listing).filter(models.Listing.id == listing_id).first()

def delete_listing(db: Session, listing_id: int):
    listing = get_listing(db, listing_id)
    if listing:
        db.delete(listing)
        db.commit()
    return listing

def update_listing(db: Session, listing_id: int, listing_data: schemas.ListingUpdate):
    listing = get_listing(db, listing_id)
    if not listing:
        return None

    listing.region_id = listing_data.region_id
    listing.price = listing_data.price
    listing.bedrooms = listing_data.bedrooms
    listing.listing_type = listing_data.listing_type

    db.commit()
    db.refresh(listing)
    return listing
