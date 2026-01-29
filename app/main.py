from fastapi import FastAPI
from .database import Base, engine
from .routers import listings, regions, analytics

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Housing Market & Rental Insights API",
    description="A data-driven API providing housing affordability and market analytics",
    version="1.0.0"
)

app.include_router(regions.router, prefix="/regions", tags=["Regions"])
app.include_router(listings.router, prefix="/listings", tags=["Listings"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
