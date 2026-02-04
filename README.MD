# Housing Market & Rental Insights API
A data-driven web API that provides analytical insights into housing affordability and rental markets using regional income and rental data

## Features
- CRUD operations for regions and housing listings
- Median rent analytics per region
- Affordability index combining rent and income data
- Comparative affordability rankings across regions
- RESTful API with OpenAPI Swagger documentation

## Technologies stack
- Python 3
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

## Architecture
The system is structured using a separation-of-concerns approach:
- Database models define persistent data
- CRUD and analytics logic are decoupled from routing
- API routers expose functionality via RESTful endpoints

## Setup Instructions

```bash
pip3 install -r requirements.txt
python3 -m uvicorn app.main:app --reload
