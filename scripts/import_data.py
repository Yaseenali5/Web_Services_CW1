import argparse
import csv
from dataclasses import dataclass
from typing import Dict

from app.database import SessionLocal
from app import models


ALLOWED_LISTING_TYPES = {"rent", "sale"}


@dataclass
class ImportStats:
    created: int = 0
    updated: int = 0
    skipped: int = 0


def import_regions_csv(path: str) -> ImportStats:
    stats = ImportStats()
    db = SessionLocal()
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("name") or "").strip()
                ons_code = (row.get("ons_code") or "").strip()
                average_income_raw = (row.get("average_income") or "").strip()

                if not name or not ons_code or not average_income_raw:
                    stats.skipped += 1
                    continue

                try:
                    average_income = float(average_income_raw)
                except ValueError:
                    stats.skipped += 1
                    continue

                if average_income <= 0:
                    stats.skipped += 1
                    continue

                region = db.query(models.Region).filter(models.Region.ons_code == ons_code).first()
                if region:
                    region.name = name
                    region.average_income = average_income
                    stats.updated += 1
                else:
                    db.add(
                        models.Region(
                            name=name,
                            ons_code=ons_code,
                            average_income=average_income,
                        )
                    )
                    stats.created += 1

        db.commit()
        return stats
    finally:
        db.close()


def import_listings_csv(path: str) -> ImportStats:
    stats = ImportStats()
    db = SessionLocal()
    try:
        regions_by_ons: Dict[str, int] = {
            r.ons_code: r.id for r in db.query(models.Region).all()
        }

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                region_ons_code = (row.get("region_ons_code") or "").strip()
                price_raw = (row.get("price") or "").strip()
                bedrooms_raw = (row.get("bedrooms") or "").strip()
                listing_type = (row.get("listing_type") or "").strip().lower()

                if not region_ons_code or not price_raw or not bedrooms_raw or not listing_type:
                    stats.skipped += 1
                    continue

                if listing_type not in ALLOWED_LISTING_TYPES:
                    stats.skipped += 1
                    continue

                region_id = regions_by_ons.get(region_ons_code)
                if not region_id:
                    stats.skipped += 1
                    continue

                try:
                    price = float(price_raw)
                    bedrooms = int(bedrooms_raw)
                except ValueError:
                    stats.skipped += 1
                    continue

                if price <= 0 or bedrooms < 0:
                    stats.skipped += 1
                    continue

                db.add(
                    models.Listing(
                        region_id=region_id,
                        price=price,
                        bedrooms=bedrooms,
                        listing_type=listing_type,
                    )
                )
                stats.created += 1

        db.commit()
        return stats
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import regions and listings from CSV files into SQLite."
    )
    parser.add_argument("--regions", required=True, help="Path to regions CSV")
    parser.add_argument("--listings", required=True, help="Path to listings CSV")
    args = parser.parse_args()

    region_stats = import_regions_csv(args.regions)
    listing_stats = import_listings_csv(args.listings)

    print(
        "Regions: "
        f"created={region_stats.created}, updated={region_stats.updated}, skipped={region_stats.skipped}"
    )
    print(
        "Listings: "
        f"created={listing_stats.created}, updated={listing_stats.updated}, skipped={listing_stats.skipped}"
    )


if __name__ == "__main__":
    main()
