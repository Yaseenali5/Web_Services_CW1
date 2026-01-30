from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Listing, status_code=status.HTTP_201_CREATED)
def create_listing(listing: schemas.ListingCreate, db: Session = Depends(get_db)):
    return crud.create_listing(db, listing)

@router.get("/", response_model=list[schemas.Listing])
def read_listings(db: Session = Depends(get_db)):
    return crud.get_listings(db)

@router.get("/{listing_id}", response_model=schemas.Listing)
def read_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = crud.get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = crud.delete_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
