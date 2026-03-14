import argparse
import csv
import json
import os
import urllib.request
from collections import Counter


def load_registry(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def download_file(url: str, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with urllib.request.urlopen(url) as response:
        data = response.read()
    with open(out_path, "wb") as f:
        f.write(data)


def explore_csv(path: str, sample_rows: int = 5) -> dict:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = []
        null_counts = Counter({name: 0 for name in fieldnames})
        total_rows = 0
        for row in reader:
            total_rows += 1
            if len(rows) < sample_rows:
                rows.append(row)
            for key in fieldnames:
                if (row.get(key) or "").strip() == "":
                    null_counts[key] += 1

    return {
        "file": path,
        "columns": fieldnames,
        "total_rows": total_rows,
        "sample_rows": rows,
        "null_counts": dict(null_counts),
    }


def print_exploration(summary: dict) -> None:
    print(f"File: {summary['file']}")
    print(f"Columns ({len(summary['columns'])}): {', '.join(summary['columns'])}")
    print(f"Total rows: {summary['total_rows']}")
    print("Sample rows:")
    for i, row in enumerate(summary["sample_rows"], start=1):
        print(f"  [{i}] {row}")
    print("Null counts by column:")
    for key, value in summary["null_counts"].items():
        print(f"  - {key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and explore a public CSV dataset."
    )
    parser.add_argument("--url", default="", help="Direct CSV URL")
    parser.add_argument("--dataset-id", default="", help="Dataset id from registry")
    parser.add_argument(
        "--registry",
        default="data/dataset_registry.json",
        help="Path to dataset registry JSON",
    )
    parser.add_argument("--out", required=True, help="Where to save downloaded CSV")
    parser.add_argument("--sample-rows", type=int, default=5, help="Number of sample rows to print")
    args = parser.parse_args()

    url = args.url
    if args.dataset_id:
        registry = load_registry(args.registry)
        match = next((d for d in registry.get("datasets", []) if d.get("id") == args.dataset_id), None)
        if not match:
            raise ValueError(f"Dataset id not found in registry: {args.dataset_id}")
        url = match["csv_url"]
        print(f"Using dataset: {match['name']}")
        print(f"Provider: {match['provider']}")
        print(f"License: {match['license']} ({match['license_url']})")

    if not url:
        raise ValueError("Provide --url or --dataset-id")

    download_file(url, args.out)
    summary = explore_csv(args.out, sample_rows=args.sample_rows)
    print_exploration(summary)


if __name__ == "__main__":
    main()
