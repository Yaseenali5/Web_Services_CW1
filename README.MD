# Housing Market & Rental Insights API

A FastAPI + SQLite project for storing housing data and computing affordability analytics.

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Run Tests

```bash
python3 -m unittest discover -s tests -v
```

## Import Sample Data

```bash
python3 scripts/import_data.py --regions data/sample_regions.csv --listings data/sample_listings.csv --manifest data/ingestion_manifest.json
```

## Prepare External Dataset

```bash
python3 scripts/prepare_external_dataset.py \
  --source-csv path/to/external_housing_data.csv \
  --out-regions data/prepared_regions.csv \
  --out-listings data/prepared_listings.csv
```

Then import:
```bash
python3 scripts/import_data.py --regions data/prepared_regions.csv --listings data/prepared_listings.csv --manifest data/ingestion_manifest.json
```

## Benchmark Key Endpoints

```bash
python3 scripts/benchmark_api.py --iterations 50
```

## Authentication

Write operations (POST, PUT, DELETE) require a Bearer token with the write scope.

- Get bearer token (demo credentials):
```bash
curl -X POST http://127.0.0.1:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=adminpass"
```
- Use token for write requests:
```bash
curl -X POST http://127.0.0.1:8000/regions/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Leeds","ons_code":"E08000035","average_income":29500}'
```

## Documentation

- Markdown API documentation: `API_DOCUMENTATION.md`
- Submission-ready API documentation PDF: `API_DOCUMENTATION.pdf`

## Project Structure

```text
app/
  main.py
  models.py
  schemas.py
  database.py
  crud.py
  analytics.py
  routers/
    regions.py
    listings.py
    analytics.py
```

## API Endpoints

### Regions

- `POST /regions/` Create region
- `GET /regions/` List regions
- `GET /regions/{region_id}` Get one region
- `PUT /regions/{region_id}` Update region
- `DELETE /regions/{region_id}` Delete region

### Listings

- `POST /listings/` Create listing
- `GET /listings/` List listings
- `GET /listings/{listing_id}` Get one listing
- `PUT /listings/{listing_id}` Update listing
- `DELETE /listings/{listing_id}` Delete listing

### Analytics

- `GET /analytics/` Analytics root message
- `GET /analytics/regions/{region_id}/median-rent` Median monthly rent for region
- `GET /analytics/regions/{region_id}/affordability` Affordability index and class
- `GET /analytics/affordability/rankings` Cross-region affordability ranking
- `GET /analytics/regions/{region_id}/affordability/simulate
- `GET /analytics/regions/{region_id}/price-trend
- `GET /analytics/regions/{region_id}/risk-score


## Example Payloads

### Create Region

```json
{
  "name": "Leeds",
  "ons_code": "E08000035",
  "average_income": 29500
}
```

### Create Listing

```json
{
  "region_id": 1,
  "price": 950,
  "bedrooms": 2,
  "listing_type": "rent"
}
```

## Notes

- Database file: `housing.db`
- API currently runs with local SQLite storage.
