#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


PROFILE_FIELDS = [
    "EVENT_KEY",
    "EVENT_DATE",
    "OFFENSE_CODE",
    "OFFENSE_DESC",
    "LAW_CATEGORY",
    "LATITUDE",
    "LONGITUDE",
    "TRACT_GEOID",
    "BLOCK_GROUP_GEOID",
    "PUBLIC_PERSON_ID",
    "RELATED_EVENT_KEY",
    "LINK_STATUS",
]


def frame_to_records(df: pl.DataFrame) -> list[dict[str, object]]:
    return df.to_dicts()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()

    panel_path = args.path
    if not panel_path.exists():
        raise SystemExit(f"missing panel parquet: {panel_path}")

    summary_path = Path("data/meta") / f"{panel_path.stem}_profile.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    lf = pl.scan_parquet(panel_path)

    total_rows = int(lf.select(pl.len()).collect().item())

    year_counts = (
        lf.group_by("EVENT_YEAR")
        .agg(pl.len().alias("rows"))
        .collect()
        .sort("EVENT_YEAR")
    )

    source_counts = (
        lf.group_by("EVENT_SOURCE")
        .agg(pl.len().alias("rows"))
        .collect()
        .sort("EVENT_SOURCE")
    )

    geography_by_year = (
        lf.group_by("EVENT_YEAR")
        .agg(
            pl.len().alias("rows"),
            pl.col("CENSUS_MATCH_STATUS").is_not_null().sum().alias("rows_with_census_status"),
            pl.col("TRACT_GEOID").is_not_null().sum().alias("rows_with_tract"),
            pl.col("BLOCK_GROUP_GEOID").is_not_null().sum().alias("rows_with_block_group"),
        )
        .with_columns(
            (pl.col("rows_with_tract") / pl.col("rows")).alias("tract_coverage_rate"),
            (pl.col("rows_with_block_group") / pl.col("rows")).alias("block_group_coverage_rate"),
        )
        .collect()
        .sort("EVENT_YEAR")
    )

    geography_by_source = (
        lf.group_by("EVENT_SOURCE")
        .agg(
            pl.len().alias("rows"),
            pl.col("CENSUS_MATCH_STATUS").is_not_null().sum().alias("rows_with_census_status"),
            pl.col("TRACT_GEOID").is_not_null().sum().alias("rows_with_tract"),
            pl.col("BLOCK_GROUP_GEOID").is_not_null().sum().alias("rows_with_block_group"),
        )
        .with_columns(
            (pl.col("rows_with_tract") / pl.col("rows")).alias("tract_coverage_rate"),
            (pl.col("rows_with_block_group") / pl.col("rows")).alias("block_group_coverage_rate"),
        )
        .collect()
        .sort("EVENT_SOURCE")
    )

    non_null_by_source = (
        lf.group_by("EVENT_SOURCE")
        .agg(
            pl.len().alias("rows"),
            *[
                pl.col(field).is_not_null().sum().alias(f"{field}_non_null")
                for field in PROFILE_FIELDS
            ],
        )
        .collect()
        .sort("EVENT_SOURCE")
    )

    link_status_by_year = (
        lf.filter(pl.col("EVENT_SOURCE") == "nypd_arrests")
        .group_by(["EVENT_YEAR", "LINK_STATUS"])
        .agg(pl.len().alias("rows"))
        .collect()
        .sort(["EVENT_YEAR", "LINK_STATUS"])
    )

    census_status_counts = (
        lf.group_by("CENSUS_MATCH_STATUS")
        .agg(pl.len().alias("rows"))
        .collect()
        .sort("CENSUS_MATCH_STATUS")
    )

    summary = {
        "input_path": str(panel_path),
        "total_rows": total_rows,
        "year_counts": frame_to_records(year_counts),
        "source_counts": frame_to_records(source_counts),
        "geography_by_year": frame_to_records(geography_by_year),
        "geography_by_source": frame_to_records(geography_by_source),
        "non_null_by_source": frame_to_records(non_null_by_source),
        "link_status_by_year": frame_to_records(link_status_by_year),
        "census_status_counts": frame_to_records(census_status_counts),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
