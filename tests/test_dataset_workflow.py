import csv
import json
import os
import tempfile
import unittest

from scripts.download_and_explore import load_registry, explore_csv
from scripts.merge_ons_with_profiles import build_staging_from_ons
from scripts.prepare_external_dataset import normalize_dataset


class DatasetWorkflowTestCase(unittest.TestCase):
    def test_registry_loads_and_contains_license(self):
        registry = load_registry("data/dataset_registry.json")
        self.assertIn("datasets", registry)
        self.assertGreaterEqual(len(registry["datasets"]), 1)
        first = registry["datasets"][0]
        self.assertIn("id", first)
        self.assertIn("csv_url", first)
        self.assertIn("license", first)
        self.assertIn("license_url", first)

    def test_explore_csv_returns_summary(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["region_name", "value"])
            writer.writerow(["Leeds", "1"])
            writer.writerow(["", "2"])

        summary = explore_csv(path, sample_rows=2)
        self.assertEqual(summary["total_rows"], 2)
        self.assertEqual(summary["columns"], ["region_name", "value"])
        self.assertEqual(len(summary["sample_rows"]), 2)
        self.assertEqual(summary["null_counts"]["region_name"], 1)

    def test_ons_merge_then_normalize_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ons_path = os.path.join(tmpdir, "ons.csv")
            profiles_path = os.path.join(tmpdir, "profiles.csv")
            staging_path = os.path.join(tmpdir, "staging.csv")
            out_regions = os.path.join(tmpdir, "prepared_regions.csv")
            out_listings = os.path.join(tmpdir, "prepared_listings.csv")

            with open(ons_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "geography code", "value"])
                writer.writerow(["2024-01", "E08000035", "100.0"])
                writer.writerow(["2024-02", "E08000035", "105.0"])  # latest for Leeds
                writer.writerow(["2024-01", "E08000003", "98.0"])

            with open(profiles_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "region_ons_code",
                        "region_name",
                        "average_income",
                        "bedrooms",
                        "listing_type",
                        "base_monthly_rent",
                    ]
                )
                writer.writerow(["E08000035", "Leeds", "30000", "2", "rent", "900"])
                writer.writerow(["E08000003", "Manchester", "32000", "2", "rent", "950"])

            merge_stats = build_staging_from_ons(
                ons_csv=ons_path,
                profiles_csv=profiles_path,
                out_staging_csv=staging_path,
            )
            self.assertEqual(merge_stats.written_rows, 2)

            prep_stats = normalize_dataset(
                source_csv=staging_path,
                out_regions_csv=out_regions,
                out_listings_csv=out_listings,
            )
            self.assertEqual(prep_stats.written_regions, 2)
            self.assertEqual(prep_stats.written_listings, 2)

    def test_ons_real_header_format_is_supported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ons_path = os.path.join(tmpdir, "ons_real.csv")
            profiles_path = os.path.join(tmpdir, "profiles.csv")
            staging_path = os.path.join(tmpdir, "staging.csv")

            with open(ons_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "v4_1",
                        "Data Marking",
                        "mmm-yy",
                        "Time",
                        "administrative-geography",
                        "Geography",
                        "index-and-year-change",
                        "IndexAndYearChange",
                    ]
                )
                writer.writerow(["105.0", "", "Jan-24", "Jan-24", "E08000035", "Leeds", "index", "Index"])
                writer.writerow(["4.0", "", "Jan-24", "Jan-24", "E08000035", "Leeds", "year-on-year-change", "Year-on-year change"])
                writer.writerow(["98.0", "", "Jan-24", "Jan-24", "E08000003", "Manchester", "index", "Index"])

            with open(profiles_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "region_ons_code",
                        "region_name",
                        "average_income",
                        "bedrooms",
                        "listing_type",
                        "base_monthly_rent",
                    ]
                )
                writer.writerow(["E08000035", "Leeds", "30000", "2", "rent", "900"])
                writer.writerow(["E08000003", "Manchester", "32000", "2", "rent", "950"])

            stats = build_staging_from_ons(
                ons_csv=ons_path,
                profiles_csv=profiles_path,
                out_staging_csv=staging_path,
            )
            self.assertEqual(stats.written_rows, 2)


if __name__ == "__main__":
    unittest.main()
