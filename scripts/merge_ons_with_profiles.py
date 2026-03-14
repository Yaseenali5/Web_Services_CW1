import argparse
import csv
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple


@dataclass
class MergeStats:
    ons_rows_read: int = 0
    profile_rows_read: int = 0
    written_rows: int = 0
    skipped_ons_rows: int = 0
    skipped_profile_rows: int = 0
    unmatched_ons_rows: int = 0


def _pick_column(fieldnames: List[str], candidates: List[str]) -> str:
    normalized = {name.strip().lower(): name for name in fieldnames}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in normalized:
            return normalized[key]
    raise ValueError(f"Could not find expected column. Tried: {candidates}")


def _pick_column_optional(fieldnames: List[str], candidates: List[str]) -> str:
    try:
        return _pick_column(fieldnames, candidates)
    except ValueError:
        return ""


def _parse_float(raw: str) -> float:
    return float((raw or "").strip())


def _parse_optional_date(raw: str) -> datetime:
    value = (raw or "").strip()
    if not value:
        return datetime.min
    # Accept common ONS date layouts; fallback to lexical timestamp bucket.
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y %b", "%b %Y", "%b-%y", "%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.min


def load_profiles(path: str, stats: MergeStats) -> Dict[str, Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {
            "region_ons_code",
            "region_name",
            "average_income",
            "bedrooms",
            "listing_type",
            "base_monthly_rent",
        }
        missing = required.difference(set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"Profiles CSV missing required columns: {sorted(missing)}")

        profiles: Dict[str, Dict[str, str]] = {}
        for row in reader:
            stats.profile_rows_read += 1
            try:
                ons_code = row["region_ons_code"].strip()
                region_name = row["region_name"].strip()
                average_income = _parse_float(row["average_income"])
                bedrooms = int(row["bedrooms"].strip())
                listing_type = row["listing_type"].strip().lower()
                base_monthly_rent = _parse_float(row["base_monthly_rent"])
            except Exception:
                stats.skipped_profile_rows += 1
                continue

            if (
                not ons_code
                or not region_name
                or average_income <= 0
                or bedrooms < 0
                or listing_type not in {"rent", "sale"}
                or base_monthly_rent <= 0
            ):
                stats.skipped_profile_rows += 1
                continue

            profiles[ons_code] = {
                "region_name": region_name,
                "average_income": str(average_income),
                "bedrooms": str(bedrooms),
                "listing_type": listing_type,
                "base_monthly_rent": str(base_monthly_rent),
            }
    return profiles


def _latest_index_by_region(
    ons_csv: str,
    code_column: str,
    value_column: str,
    date_column: str,
    indicator_column: str,
    stats: MergeStats,
) -> Dict[str, float]:
    latest: Dict[str, Tuple[datetime, float]] = {}
    with open(ons_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats.ons_rows_read += 1
            try:
                ons_code = row[code_column].strip()
                index_value = _parse_float(row[value_column])
                ts = _parse_optional_date(row.get(date_column, ""))
            except Exception:
                stats.skipped_ons_rows += 1
                continue

            # ONS files can mix "index" and "year-on-year-change" rows.
            if indicator_column:
                marker = (row.get(indicator_column) or "").strip().lower()
                if marker and "index" not in marker:
                    continue

            if not ons_code or index_value <= 0:
                stats.skipped_ons_rows += 1
                continue
            current = latest.get(ons_code)
            if current is None or ts >= current[0]:
                latest[ons_code] = (ts, index_value)
    return {code: pair[1] for code, pair in latest.items()}


def build_staging_from_ons(
    ons_csv: str,
    profiles_csv: str,
    out_staging_csv: str,
) -> MergeStats:
    stats = MergeStats()
    profiles = load_profiles(profiles_csv, stats)

    with open(ons_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        code_column = _pick_column(
            fields,
            [
                "geography code",
                "geography_code",
                "ons_code",
                "region_ons_code",
                "code",
                "administrative-geography",
            ],
        )
        value_column = _pick_column(fields, ["value", "v4_1", "index", "iprhp_index"])
        date_column = _pick_column_optional(fields, ["date", "time", "period", "mmm-yy"])
        indicator_column = _pick_column_optional(
            fields,
            ["index-and-year-change", "indexandyearchange"],
        )

    latest_index = _latest_index_by_region(
        ons_csv=ons_csv,
        code_column=code_column,
        value_column=value_column,
        date_column=date_column,
        indicator_column=indicator_column,
        stats=stats,
    )

    os.makedirs(os.path.dirname(out_staging_csv) or ".", exist_ok=True)
    with open(out_staging_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "region_name",
                "region_ons_code",
                "average_income",
                "monthly_price",
                "bedrooms",
                "listing_type",
            ],
        )
        writer.writeheader()
        for ons_code, idx in sorted(latest_index.items()):
            profile = profiles.get(ons_code)
            if not profile:
                stats.unmatched_ons_rows += 1
                continue

            base_monthly_rent = float(profile["base_monthly_rent"])
            monthly_price = base_monthly_rent * (idx / 100.0)
            if monthly_price <= 0:
                continue

            writer.writerow(
                {
                    "region_name": profile["region_name"],
                    "region_ons_code": ons_code,
                    "average_income": profile["average_income"],
                    "monthly_price": f"{monthly_price:.2f}",
                    "bedrooms": profile["bedrooms"],
                    "listing_type": profile["listing_type"],
                }
            )
            stats.written_rows += 1
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge ONS rental index data with region profiles into a staging CSV."
    )
    parser.add_argument("--ons-csv", required=True, help="Path to downloaded ONS CSV")
    parser.add_argument(
        "--profiles-csv",
        required=True,
        help="Path to supplemental region profile CSV (income/bedrooms/listing_type/base rent).",
    )
    parser.add_argument(
        "--out-staging",
        required=True,
        help="Output path for staging CSV expected by prepare_external_dataset.py",
    )
    args = parser.parse_args()

    stats = build_staging_from_ons(
        ons_csv=args.ons_csv,
        profiles_csv=args.profiles_csv,
        out_staging_csv=args.out_staging,
    )
    print(
        "Merged staging dataset: "
        f"ons_rows_read={stats.ons_rows_read}, profile_rows_read={stats.profile_rows_read}, "
        f"written_rows={stats.written_rows}, skipped_ons_rows={stats.skipped_ons_rows}, "
        f"skipped_profile_rows={stats.skipped_profile_rows}, unmatched_ons_rows={stats.unmatched_ons_rows}"
    )


if __name__ == "__main__":
    main()
