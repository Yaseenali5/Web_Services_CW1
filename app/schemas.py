from typing import Literal, Optional
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


class AnalyticsRootResponse(BaseModel):
    message: str


class MedianRentResponse(BaseModel):
    region_id: int
    median_rent: float


class AffordabilityResult(BaseModel):
    region: str
    median_monthly_rent: float
    median_annual_rent: float
    average_income: float
    affordability_index: float
    classification: str


class SimulationSnapshot(BaseModel):
    median_monthly_rent: Optional[float] = None
    monthly_rent: Optional[float] = None
    average_income: float
    rent_change_pct: Optional[float] = None
    income_change_pct: Optional[float] = None
    affordability_index: float
    classification: str


class SimulationDelta(BaseModel):
    index_change: float
    classification_changed: bool


class AffordabilitySimulationResponse(BaseModel):
    region: str
    baseline: SimulationSnapshot
    scenario: SimulationSnapshot
    delta: SimulationDelta


class PriceTrendPoint(BaseModel):
    bedrooms: int
    listing_count: int
    avg_price: float
    min_price: float
    max_price: float


class PriceTrendResponse(BaseModel):
    region: str
    listing_type_filter: Optional[str] = None
    total_listings: int
    overall_avg_price: float
    overall_min_price: float
    overall_max_price: float
    by_bedrooms: list[PriceTrendPoint]
