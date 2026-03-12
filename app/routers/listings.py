from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import crud, schemas
from ..database import get_db
from ..security import require_write_access

router = APIRouter()

@router.post("/", response_model=schemas.Listing, status_code=status.HTTP_201_CREATED)
def create_listing(listing: schemas.ListingCreate, db: Session = Depends(get_db), _: dict = Depends(require_write_access)):
    if not crud.get_region(db, listing.region_id):
        raise HTTPException(status_code=404, detail="Region not found")

    try:
        return crud.create_listing(db, listing)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Listing could not be created due to data integrity constraints")

@router.get("/", response_model=list[schemas.Listing])
def read_listings(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    region_id: Optional[int] = Query(default=None, gt=0),
    listing_type: Optional[str] = Query(default=None, pattern="^(rent|sale)$"),
    min_price: Optional[float] = Query(default=None, gt=0),
    max_price: Optional[float] = Query(default=None, gt=0),
    bedrooms: Optional[int] = Query(default=None, ge=0),
    sort_by: str = Query(default="id", pattern="^(id|price|bedrooms)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    return crud.get_listings(
        db=db,
        skip=skip,
        limit=limit,
        region_id=region_id,
        listing_type=listing_type,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        sort_by=sort_by,
        sort_order=sort_order,
    )

@router.get("/{listing_id}", response_model=schemas.Listing)
def read_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = crud.get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.put("/{listing_id}", response_model=schemas.Listing)
def update_listing(listing_id: int, listing: schemas.ListingUpdate, db: Session = Depends(get_db), _: dict = Depends(require_write_access)):
    if not crud.get_region(db, listing.region_id):
        raise HTTPException(status_code=404, detail="Region not found")

    try:
        updated_listing = crud.update_listing(db, listing_id, listing)
        if not updated_listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        return updated_listing
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Listing could not be updated due to data integrity constraints")

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(listing_id: int, db: Session = Depends(get_db), _: dict = Depends(require_write_access)):
    listing = crud.delete_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
