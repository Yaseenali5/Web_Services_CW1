from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import crud, schemas
from ..database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Listing, status_code=status.HTTP_201_CREATED)
def create_listing(listing: schemas.ListingCreate, db: Session = Depends(get_db)):
    if not crud.get_region(db, listing.region_id):
        raise HTTPException(status_code=404, detail="Region not found")

    try:
        return crud.create_listing(db, listing)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Listing could not be created due to data integrity constraints")

@router.get("/", response_model=list[schemas.Listing])
def read_listings(db: Session = Depends(get_db)):
    return crud.get_listings(db)

@router.get("/{listing_id}", response_model=schemas.Listing)
def read_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = crud.get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.put("/{listing_id}", response_model=schemas.Listing)
def update_listing(listing_id: int, listing: schemas.ListingUpdate, db: Session = Depends(get_db)):
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
def delete_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = crud.delete_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
