import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.database import engine
from app.models import Base


class APITestCase(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)
        self.auth = {"X-API-Key": "dev-api-key"}

    def test_write_endpoints_require_api_key(self):
        response = self.client.post(
            "/regions/",
            json={"name": "Leeds", "ons_code": "E08000035", "average_income": 29500},
        )
        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["code"], 401)

    def test_validation_errors_use_standard_shape(self):
        response = self.client.post(
            "/regions/",
            headers=self.auth,
            json={"name": "", "ons_code": "X1", "average_income": 0},
        )
        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["code"], 422)
        self.assertIn("details", payload["error"])

    def test_duplicate_region_returns_conflict(self):
        self.client.post(
            "/regions/",
            headers=self.auth,
            json={"name": "Leeds", "ons_code": "E08000035", "average_income": 29500},
        )
        response = self.client.post(
            "/regions/",
            headers=self.auth,
            json={"name": "Leeds", "ons_code": "E08000035", "average_income": 30000},
        )
        self.assertEqual(response.status_code, 409)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], 409)

    def test_listing_filters_sort_and_pagination(self):
        self.client.post(
            "/regions/",
            headers=self.auth,
            json={"name": "Leeds", "ons_code": "E08000035", "average_income": 29500},
        )
        self.client.post(
            "/regions/",
            headers=self.auth,
            json={"name": "Manchester", "ons_code": "E08000003", "average_income": 30000},
        )
        self.client.post(
            "/listings/",
            headers=self.auth,
            json={"region_id": 1, "price": 800, "bedrooms": 2, "listing_type": "rent"},
        )
        self.client.post(
            "/listings/",
            headers=self.auth,
            json={"region_id": 1, "price": 1200, "bedrooms": 3, "listing_type": "rent"},
        )
        self.client.post(
            "/listings/",
            headers=self.auth,
            json={"region_id": 2, "price": 950, "bedrooms": 2, "listing_type": "sale"},
        )

        response = self.client.get(
            "/listings/?region_id=1&listing_type=rent&sort_by=price&sort_order=desc"
        )
        self.assertEqual(response.status_code, 200)
        prices = [item["price"] for item in response.json()]
        self.assertEqual(prices, [1200.0, 800.0])

        response = self.client.get("/listings/?skip=1&limit=1&sort_by=price&sort_order=asc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["price"], 950.0)

    def test_affordability_simulation_endpoint(self):
        self.client.post(
            "/regions/",
            headers=self.auth,
            json={"name": "Leeds", "ons_code": "E08000035", "average_income": 30000},
        )
        self.client.post(
            "/listings/",
            headers=self.auth,
            json={"region_id": 1, "price": 800, "bedrooms": 2, "listing_type": "rent"},
        )
        self.client.post(
            "/listings/",
            headers=self.auth,
            json={"region_id": 1, "price": 1000, "bedrooms": 3, "listing_type": "rent"},
        )

        response = self.client.get(
            "/analytics/regions/1/affordability/simulate?rent_change_pct=10&income_change_pct=-5"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("baseline", payload)
        self.assertIn("scenario", payload)
        self.assertIn("delta", payload)


if __name__ == "__main__":
    unittest.main()
