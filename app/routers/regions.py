from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import crud, schemas
from ..database import get_db
from ..security import require_write_access

router = APIRouter()

@router.post("/", response_model=schemas.Region, status_code=status.HTTP_201_CREATED)
def create_region(region: schemas.RegionCreate, db: Session = Depends(get_db), _: dict = Depends(require_write_access)):
    try:
        return crud.create_region(db, region)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Region with same name or ONS code already exists")

@router.get("/", response_model=list[schemas.Region])
def read_regions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    name_contains: Optional[str] = None,
    sort_by: str = Query(default="id", pattern="^(id|name|average_income)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    return crud.get_regions(
        db=db,
        skip=skip,
        limit=limit,
        name_contains=name_contains,
        sort_by=sort_by,
        sort_order=sort_order,
    )

@router.get("/{region_id}", response_model=schemas.Region)
def read_region(region_id: int, db: Session = Depends(get_db)):
    region = crud.get_region(db, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region

@router.put("/{region_id}", response_model=schemas.Region)
def update_region(region_id: int, region: schemas.RegionUpdate, db: Session = Depends(get_db), _: dict = Depends(require_write_access)):
    try:
        updated_region = crud.update_region(db, region_id, region)
        if not updated_region:
            raise HTTPException(status_code=404, detail="Region not found")
        return updated_region
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Region with same name or ONS code already exists")

@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(region_id: int, db: Session = Depends(get_db), _: dict = Depends(require_write_access)):
    try:
        region = crud.delete_region(db, region_id)
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Region cannot be deleted while listings still reference it")
