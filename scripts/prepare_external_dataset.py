import argparse
import csv
import io
import os
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass
class PrepareStats:
    read_rows: int = 0
    written_regions: int = 0
    written_listings: int = 0
    skipped_rows: int = 0


def _open_source(source_csv: str = "", source_url: str = "") -> io.StringIO:
    if source_csv:
        with open(source_csv, "r", encoding="utf-8") as f:
            return io.StringIO(f.read())
    if source_url:
        with urllib.request.urlopen(source_url) as resp:
            data = resp.read().decode("utf-8")
            return io.StringIO(data)
    raise ValueError("Either source_csv or source_url must be provided")


def _safe_float(value: str) -> float:
    return float(value.strip())


def _safe_int(value: str) -> int:
    return int(value.strip())


def normalize_dataset(
    source_csv: str,
    out_regions_csv: str,
    out_listings_csv: str,
    source_url: str = "",
) -> PrepareStats:
    """
    Convert an external housing dataset into internal normalized CSVs.

    Expected input columns:
    - region_name
    - region_ons_code
    - average_income
    - monthly_price
    - bedrooms
    - listing_type
    """
    stats = PrepareStats()
    region_map: Dict[str, Dict[str, str]] = {}
    listing_rows: List[Dict[str, str]] = []

    source_stream = _open_source(source_csv=source_csv, source_url=source_url)
    reader = csv.DictReader(source_stream)
    required = {
        "region_name",
        "region_ons_code",
        "average_income",
        "monthly_price",
        "bedrooms",
        "listing_type",
    }
    missing = required.difference(set(reader.fieldnames or []))
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    for row in reader:
        stats.read_rows += 1
        try:
            region_name = row["region_name"].strip()
            ons_code = row["region_ons_code"].strip()
            average_income = _safe_float(row["average_income"])
            monthly_price = _safe_float(row["monthly_price"])
            bedrooms = _safe_int(row["bedrooms"])
            listing_type = row["listing_type"].strip().lower()
        except Exception:
            stats.skipped_rows += 1
            continue

        if not region_name or not ons_code or average_income <= 0 or monthly_price <= 0 or bedrooms < 0:
            stats.skipped_rows += 1
            continue
        if listing_type not in {"rent", "sale"}:
            stats.skipped_rows += 1
            continue

        region_map[ons_code] = {
            "name": region_name,
            "ons_code": ons_code,
            "average_income": str(average_income),
        }
        listing_rows.append(
            {
                "region_ons_code": ons_code,
                "price": str(monthly_price),
                "bedrooms": str(bedrooms),
                "listing_type": listing_type,
            }
        )

    os.makedirs(os.path.dirname(out_regions_csv) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(out_listings_csv) or ".", exist_ok=True)

    with open(out_regions_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "ons_code", "average_income"])
        writer.writeheader()
        for item in sorted(region_map.values(), key=lambda x: x["ons_code"]):
            writer.writerow(item)
            stats.written_regions += 1

    with open(out_listings_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["region_ons_code", "price", "bedrooms", "listing_type"])
        writer.writeheader()
        for item in listing_rows:
            writer.writerow(item)
            stats.written_listings += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Prepare an external housing dataset into normalized CSVs for import."
    )
    parser.add_argument("--source-csv", default="", help="Input CSV path")
    parser.add_argument("--source-url", default="", help="Input CSV URL (optional)")
    parser.add_argument("--out-regions", required=True, help="Output regions CSV path")
    parser.add_argument("--out-listings", required=True, help="Output listings CSV path")
    args = parser.parse_args()

    stats = normalize_dataset(
        source_csv=args.source_csv,
        source_url=args.source_url,
        out_regions_csv=args.out_regions,
        out_listings_csv=args.out_listings,
    )
    print(
        "Prepared dataset: "
        f"read_rows={stats.read_rows}, written_regions={stats.written_regions}, "
        f"written_listings={stats.written_listings}, skipped_rows={stats.skipped_rows}"
    )


if __name__ == "__main__":
    main()
