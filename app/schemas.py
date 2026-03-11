from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class RegionBase(BaseModel):
    name: str = Field(min_length=1)
    ons_code: str = Field(min_length=1)
    average_income: float = Field(gt=0)


class RegionCreate(RegionBase):
    pass

class RegionUpdate(RegionBase):
    pass


class Region(RegionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ListingBase(BaseModel):
    region_id: int = Field(gt=0)
    price: float = Field(gt=0)
    bedrooms: int = Field(ge=0)
    listing_type: Literal["rent", "sale"]


class ListingCreate(ListingBase):
    pass

class ListingUpdate(ListingBase):
    pass


class Listing(ListingBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
