#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


def year_range(start_year: int, end_year: int) -> list[int]:
    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")
    return list(range(start_year, end_year + 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    args = parser.parse_args()

    years = year_range(args.start_year, args.end_year)
    paths = [Path(f"data/derived/public_event_spine_{year}_census_geo.parquet") for year in years]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit(f"missing yearly census_geo spines: {', '.join(missing)}")

    out_parquet = Path(
        f"data/derived/public_event_panel_{args.start_year}_{args.end_year}_census_geo.parquet"
    )
    summary_path = Path(
        f"data/meta/public_event_panel_{args.start_year}_{args.end_year}_census_geo_summary.json"
    )
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    frames = [pl.scan_parquet(path) for path in paths]
    panel = pl.concat(frames, how="vertical_relaxed")
    panel.sink_parquet(out_parquet)

    year_counts = (
        pl.scan_parquet(out_parquet)
        .group_by("EVENT_YEAR")
        .agg(pl.len().alias("n"))
        .collect()
        .sort("EVENT_YEAR")
    )
    source_counts = (
        pl.scan_parquet(out_parquet)
        .group_by("EVENT_SOURCE")
        .agg(pl.len().alias("n"))
        .collect()
        .sort("EVENT_SOURCE")
    )

    summary = {
        "start_year": args.start_year,
        "end_year": args.end_year,
        "input_paths": [str(path) for path in paths],
        "output_parquet": str(out_parquet),
        "rows_written": int(pl.scan_parquet(out_parquet).select(pl.len()).collect().item()),
        "year_counts": dict(zip(year_counts["EVENT_YEAR"].to_list(), year_counts["n"].to_list())),
        "source_counts": dict(zip(source_counts["EVENT_SOURCE"].to_list(), source_counts["n"].to_list())),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
