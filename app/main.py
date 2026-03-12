from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .database import Base, engine
from .routers import listings, regions, analytics, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Housing Market & Rental Insights API",
    description="A data-driven API providing housing affordability and market analytics",
    version="1.0.0"
)

app.include_router(regions.router, prefix="/regions", tags=["Regions"])
app.include_router(listings.router, prefix="/listings", tags=["Listings"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": str(exc.detail),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation failed",
                "details": exc.errors(),
            }
        },
    )
