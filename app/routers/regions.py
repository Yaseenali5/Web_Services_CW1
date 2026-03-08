from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Region, status_code=status.HTTP_201_CREATED)
def create_region(region: schemas.RegionCreate, db: Session = Depends(get_db)):
    return crud.create_region(db, region)

@router.get("/", response_model=list[schemas.Region])
def read_regions(db: Session = Depends(get_db)):
    return crud.get_regions(db)

@router.get("/{region_id}", response_model=schemas.Region)
def read_region(region_id: int, db: Session = Depends(get_db)):
    region = crud.get_region(db, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region

@router.put("/{region_id}", response_model=schemas.Region)
def update_region(region_id: int, region: schemas.RegionUpdate, db: Session = Depends(get_db)):
    updated_region = crud.update_region(db, region_id, region)
    if not updated_region:
        raise HTTPException(status_code=404, detail="Region not found")
    return updated_region

@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(region_id: int, db: Session = Depends(get_db)):
    region = crud.delete_region(db, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
