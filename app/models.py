from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from .database import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    ons_code = Column(String, unique=True)
    average_income = Column(Float)

    listings = relationship("Listing", back_populates="region")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"))
    price = Column(Float)
    bedrooms = Column(Integer)
    listing_type = Column(String)  # rent or sale

    region = relationship("Region", back_populates="listings")
