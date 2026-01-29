from pydantic import BaseModel

class RegionBase(BaseModel):
    name: str
    ons_code: str
    average_income: float


class RegionCreate(RegionBase):
    pass


class Region(RegionBase):
    id: int

    class Config:
        orm_mode = True


class ListingBase(BaseModel):
    region_id: int
    price: float
    bedrooms: int
    listing_type: str


class ListingCreate(ListingBase):
    pass


class Listing(ListingBase):
    id: int

    class Config:
        orm_mode = True
