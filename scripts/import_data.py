import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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


def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def update_manifest(
    manifest_path: str,
    regions_path: str,
    regions_stats: ImportStats,
    listings_path: str,
    listings_stats: ImportStats,
):
    timestamp = datetime.now(timezone.utc).isoformat()
    manifest = {
        "generated_at_utc": timestamp,
        "sources": {
            "regions_csv": {
                "path": regions_path,
                "sha256": _file_sha256(regions_path),
                "stats": regions_stats.__dict__,
            },
            "listings_csv": {
                "path": listings_path,
                "sha256": _file_sha256(listings_path),
                "stats": listings_stats.__dict__,
            },
        },
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Import regions and listings from CSV files into SQLite."
    )
    parser.add_argument("--regions", required=True, help="Path to regions CSV")
    parser.add_argument("--listings", required=True, help="Path to listings CSV")
    parser.add_argument(
        "--manifest",
        default="data/ingestion_manifest.json",
        help="Path to ingestion metadata manifest JSON",
    )
    args = parser.parse_args()

    region_stats = import_regions_csv(args.regions)
    listing_stats = import_listings_csv(args.listings)
    update_manifest(
        manifest_path=args.manifest,
        regions_path=args.regions,
        regions_stats=region_stats,
        listings_path=args.listings,
        listings_stats=listing_stats,
    )

    print(
        "Regions: "
        f"created={region_stats.created}, updated={region_stats.updated}, skipped={region_stats.skipped}"
    )
    print(
        "Listings: "
        f"created={listing_stats.created}, updated={listing_stats.updated}, skipped={listing_stats.skipped}"
    )
    print(f"Manifest: written to {args.manifest}")


if __name__ == "__main__":
    main()
