from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from . import models, schemas

def create_region(db: Session, region: schemas.RegionCreate):
    db_region = models.Region(
        name=region.name,
        ons_code=region.ons_code,
        average_income=region.average_income
    )
    db.add(db_region)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_region)
    return db_region

def get_regions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    name_contains: Optional[str] = None,
    sort_by: str = "id",
    sort_order: str = "asc",
):
    query = db.query(models.Region)

    if name_contains:
        query = query.filter(models.Region.name.ilike(f"%{name_contains}%"))

    sort_map = {
        "id": models.Region.id,
        "name": models.Region.name,
        "average_income": models.Region.average_income,
    }
    sort_column = sort_map.get(sort_by, models.Region.id)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    return query.offset(skip).limit(limit).all()

def get_region(db: Session, region_id: int):
    return db.query(models.Region).filter(models.Region.id == region_id).first()

def delete_region(db: Session, region_id: int):
    region = get_region(db, region_id)
    if region:
        db.delete(region)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise
    return region

def update_region(db: Session, region_id: int, region_data: schemas.RegionUpdate):
    region = get_region(db, region_id)
    if not region:
        return None

    region.name = region_data.name
    region.ons_code = region_data.ons_code
    region.average_income = region_data.average_income

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_listing)
    return db_listing

def get_listings(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    region_id: Optional[int] = None,
    listing_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    sort_by: str = "id",
    sort_order: str = "asc",
):
    query = db.query(models.Listing)

    if region_id is not None:
        query = query.filter(models.Listing.region_id == region_id)
    if listing_type is not None:
        query = query.filter(models.Listing.listing_type == listing_type)
    if min_price is not None:
        query = query.filter(models.Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Listing.price <= max_price)
    if bedrooms is not None:
        query = query.filter(models.Listing.bedrooms == bedrooms)

    sort_map = {
        "id": models.Listing.id,
        "price": models.Listing.price,
        "bedrooms": models.Listing.bedrooms,
    }
    sort_column = sort_map.get(sort_by, models.Listing.id)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    return query.offset(skip).limit(limit).all()

def get_listing(db: Session, listing_id: int):
    return db.query(models.Listing).filter(models.Listing.id == listing_id).first()

def delete_listing(db: Session, listing_id: int):
    listing = get_listing(db, listing_id)
    if listing:
        db.delete(listing)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise
    return listing

def update_listing(db: Session, listing_id: int, listing_data: schemas.ListingUpdate):
    listing = get_listing(db, listing_id)
    if not listing:
        return None

    listing.region_id = listing_data.region_id
    listing.price = listing_data.price
    listing.bedrooms = listing_data.bedrooms
    listing.listing_type = listing_data.listing_type

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(listing)
    return listing
