import csv
import os
import tempfile
import unittest

from app.database import SessionLocal, engine
from app.models import Base, Region, Listing
from scripts.import_data import import_regions_csv, import_listings_csv


class ImportPipelineTestCase(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def _write_csv(self, headers, rows):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return path

    def test_regions_upsert_and_skip_invalid_rows(self):
        regions_path = self._write_csv(
            ["name", "ons_code", "average_income"],
            [
                ["Leeds", "E08000035", "29500"],
                ["Manchester", "E08000003", "28000"],
                ["BadIncome", "BAD001", "-1"],
                ["MissingCode", "", "25000"],
            ],
        )
        stats_first = import_regions_csv(regions_path)
        self.assertEqual(stats_first.created, 2)
        self.assertEqual(stats_first.updated, 0)
        self.assertEqual(stats_first.skipped, 2)

        regions_path_updated = self._write_csv(
            ["name", "ons_code", "average_income"],
            [
                ["Leeds Updated", "E08000035", "30000"],
            ],
        )
        stats_second = import_regions_csv(regions_path_updated)
        self.assertEqual(stats_second.created, 0)
        self.assertEqual(stats_second.updated, 1)
        self.assertEqual(stats_second.skipped, 0)

        db = SessionLocal()
        try:
            regions = db.query(Region).order_by(Region.ons_code.asc()).all()
            self.assertEqual(len(regions), 2)
            leeds = db.query(Region).filter(Region.ons_code == "E08000035").first()
            self.assertEqual(leeds.name, "Leeds Updated")
            self.assertEqual(leeds.average_income, 30000.0)
        finally:
            db.close()

    def test_listings_import_and_skip_invalid_rows(self):
        regions_path = self._write_csv(
            ["name", "ons_code", "average_income"],
            [
                ["Leeds", "E08000035", "29500"],
                ["Manchester", "E08000003", "28000"],
            ],
        )
        import_regions_csv(regions_path)

        listings_path = self._write_csv(
            ["region_ons_code", "price", "bedrooms", "listing_type"],
            [
                ["E08000035", "800", "2", "rent"],
                ["E08000035", "1200", "3", "rent"],
                ["E08000003", "950", "2", "sale"],
                ["MISSING", "900", "2", "rent"],  # unknown region
                ["E08000035", "-1", "2", "rent"],  # invalid price
                ["E08000035", "900", "-1", "rent"],  # invalid bedrooms
                ["E08000035", "900", "2", "lease"],  # invalid listing_type
            ],
        )
        stats = import_listings_csv(listings_path)
        self.assertEqual(stats.created, 3)
        self.assertEqual(stats.updated, 0)
        self.assertEqual(stats.skipped, 4)

        db = SessionLocal()
        try:
            listings = db.query(Listing).all()
            self.assertEqual(len(listings), 3)
            self.assertTrue(all(item.listing_type in {"rent", "sale"} for item in listings))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
