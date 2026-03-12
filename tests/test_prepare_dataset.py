import csv
import os
import tempfile
import unittest

from scripts.prepare_external_dataset import normalize_dataset


class PrepareDatasetTestCase(unittest.TestCase):
    def _write_csv(self, headers, rows):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return path

    def test_normalize_dataset_outputs_expected_rows(self):
        source = self._write_csv(
            ["region_name", "region_ons_code", "average_income", "monthly_price", "bedrooms", "listing_type"],
            [
                ["Leeds", "E08000035", "30000", "900", "2", "rent"],
                ["Leeds", "E08000035", "30000", "1100", "3", "rent"],
                ["Manchester", "E08000003", "28000", "950", "2", "sale"],
                ["Bad", "BAD", "-1", "100", "1", "rent"],  # invalid
            ],
        )

        out_regions = tempfile.mktemp(suffix="_regions.csv")
        out_listings = tempfile.mktemp(suffix="_listings.csv")

        stats = normalize_dataset(
            source_csv=source,
            source_url="",
            out_regions_csv=out_regions,
            out_listings_csv=out_listings,
        )

        self.assertEqual(stats.read_rows, 4)
        self.assertEqual(stats.written_regions, 2)
        self.assertEqual(stats.written_listings, 3)
        self.assertEqual(stats.skipped_rows, 1)

        with open(out_regions, newline="", encoding="utf-8") as f:
            regions = list(csv.DictReader(f))
        with open(out_listings, newline="", encoding="utf-8") as f:
            listings = list(csv.DictReader(f))

        self.assertEqual(len(regions), 2)
        self.assertEqual(len(listings), 3)
        self.assertEqual(sorted(r["ons_code"] for r in regions), ["E08000003", "E08000035"])


if __name__ == "__main__":
    unittest.main()
