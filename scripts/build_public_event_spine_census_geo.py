#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import tempfile
from pathlib import Path

import polars as pl


URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinatesbatch"
BENCHMARK = "Public_AR_Current"
VINTAGE = "Current_Current"
BATCH_SIZE = 10000

CACHE_SCHEMA = {
    "COORD_ID": pl.Utf8,
    "LONGITUDE": pl.Utf8,
    "LATITUDE": pl.Utf8,
    "CENSUS_MATCH_STATUS": pl.Utf8,
    "STATE_FIPS": pl.Utf8,
    "COUNTY_FIPS": pl.Utf8,
    "COUNTY_GEOID": pl.Utf8,
    "TRACT_CODE": pl.Utf8,
    "TRACT_GEOID": pl.Utf8,
    "BLOCK_GROUP": pl.Utf8,
    "BLOCK_GROUP_GEOID": pl.Utf8,
    "BLOCK_CODE": pl.Utf8,
    "BLOCK_GEOID": pl.Utf8,
}

GEO_COLUMNS = [
    "CENSUS_MATCH_STATUS",
    "STATE_FIPS",
    "COUNTY_FIPS",
    "COUNTY_GEOID",
    "TRACT_CODE",
    "TRACT_GEOID",
    "BLOCK_GROUP",
    "BLOCK_GROUP_GEOID",
    "BLOCK_CODE",
    "BLOCK_GEOID",
]


def coord_id(lon: str, lat: str) -> str:
    return f"{lon}|{lat}"


def chunked(seq: list[tuple[str, str, str]], size: int):
    for start in range(0, len(seq), size):
        yield seq[start : start + size]


def empty_cache_df() -> pl.DataFrame:
    return pl.DataFrame(schema=CACHE_SCHEMA)


def load_cache(cache_path: Path) -> pl.DataFrame:
    if not cache_path.exists():
        return empty_cache_df()
    return pl.read_csv(cache_path, schema_overrides=CACHE_SCHEMA)


def load_seed_cache(cache_path: Path) -> tuple[pl.DataFrame, list[str]]:
    if cache_path.exists():
        return load_cache(cache_path).unique(subset=["COORD_ID"], keep="last"), []

    legacy_paths = sorted(cache_path.parent.glob("public_event_spine_*_unique_coords_census.csv"))
    legacy_frames = [load_cache(path) for path in legacy_paths if path.exists()]
    if not legacy_frames:
        return empty_cache_df(), []

    return (
        pl.concat(legacy_frames, how="diagonal_relaxed").unique(subset=["COORD_ID"], keep="last"),
        [str(path) for path in legacy_paths],
    )


def geocode_batch(rows: list[tuple[str, str, str]]) -> list[dict[str, str]]:
    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = Path(tmpdir) / "coords.csv"
        out_path = Path(tmpdir) / "out.csv"

        with in_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerows(rows)

        subprocess.run(
            [
                "curl",
                "--silent",
                "--show-error",
                "--fail",
                "--form",
                f"coordinatesFile=@{in_path}",
                "--form",
                f"benchmark={BENCHMARK}",
                "--form",
                f"vintage={VINTAGE}",
                URL,
                "-o",
                str(out_path),
            ],
            check=True,
        )

        parsed_rows: list[dict[str, str]] = []
        with out_path.open(newline="") as fh:
            reader = csv.reader(fh)
            for row in reader:
                if len(row) < 4:
                    continue
                rec_id, lon, lat, match = row[:4]
                state = row[4] if len(row) > 4 else ""
                county = row[5] if len(row) > 5 else ""
                tract = row[6] if len(row) > 6 else ""
                block = row[7] if len(row) > 7 else ""
                county_geoid = f"{state}{county}" if state and county else ""
                tract_geoid = f"{county_geoid}{tract}" if county_geoid and tract else ""
                block_group = block[:1] if block else ""
                block_group_geoid = f"{tract_geoid}{block_group}" if tract_geoid and block_group else ""
                block_geoid = f"{tract_geoid}{block}" if tract_geoid and block else ""
                parsed_rows.append(
                    {
                        "COORD_ID": rec_id,
                        "LONGITUDE": lon,
                        "LATITUDE": lat,
                        "CENSUS_MATCH_STATUS": match,
                        "STATE_FIPS": state,
                        "COUNTY_FIPS": county,
                        "COUNTY_GEOID": county_geoid,
                        "TRACT_CODE": tract,
                        "TRACT_GEOID": tract_geoid,
                        "BLOCK_GROUP": block_group,
                        "BLOCK_GROUP_GEOID": block_group_geoid,
                        "BLOCK_CODE": block,
                        "BLOCK_GEOID": block_geoid,
                    }
                )
        return parsed_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--cache-path", type=Path, default=Path("data/meta/census_unique_coords_cache.csv"))
    parser.add_argument("--write-csv", action="store_true")
    args = parser.parse_args()
    year = args.year

    spine_path = Path(f"data/derived/public_event_spine_{year}.parquet")
    out_parquet = Path(f"data/derived/public_event_spine_{year}_census_geo.parquet")
    out_csv = Path(f"data/derived/public_event_spine_{year}_census_geo.csv") if args.write_csv else None
    summary_path = Path(f"data/meta/public_event_spine_{year}_census_geo_summary.json")
    cache_path = args.cache_path

    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    spine = pl.scan_parquet(spine_path).with_columns(
        pl.col("LONGITUDE").cast(pl.Utf8).str.strip_chars().alias("LONGITUDE"),
        pl.col("LATITUDE").cast(pl.Utf8).str.strip_chars().alias("LATITUDE"),
    )

    total_rows = int(spine.select(pl.len()).collect().item())
    rows_with_coords = int(
        spine.filter(
            pl.col("LONGITUDE").is_not_null()
            & (pl.col("LONGITUDE") != "")
            & pl.col("LATITUDE").is_not_null()
            & (pl.col("LATITUDE") != "")
        )
        .select(pl.len())
        .collect()
        .item()
    )

    unique_coords = (
        spine.filter(
            pl.col("LONGITUDE").is_not_null()
            & (pl.col("LONGITUDE") != "")
            & pl.col("LATITUDE").is_not_null()
            & (pl.col("LATITUDE") != "")
        )
        .select("LONGITUDE", "LATITUDE")
        .unique()
        .with_columns(pl.concat_str(["LONGITUDE", "LATITUDE"], separator="|").alias("COORD_ID"))
        .collect()
    )

    cache_before, seeded_cache_paths = load_seed_cache(cache_path)

    missing_coords = (
        unique_coords.lazy()
        .join(cache_before.lazy().select("COORD_ID"), on="COORD_ID", how="anti")
        .collect()
    )

    missing_rows = [
        (row["COORD_ID"], row["LONGITUDE"], row["LATITUDE"])
        for row in missing_coords.iter_rows(named=True)
    ]

    new_cache_rows: list[dict[str, str]] = []
    total_batches = math.ceil(len(missing_rows) / BATCH_SIZE) if missing_rows else 0
    for idx, batch in enumerate(chunked(missing_rows, BATCH_SIZE), start=1):
        print(f"geocoding batch {idx}/{total_batches} size={len(batch)}", flush=True)
        new_cache_rows.extend(geocode_batch(batch))

    if new_cache_rows:
        cache_after = pl.concat(
            [cache_before, pl.DataFrame(new_cache_rows, schema=CACHE_SCHEMA)],
            how="diagonal_relaxed",
        ).unique(subset=["COORD_ID"], keep="last")
    else:
        cache_after = cache_before

    cache_after.write_csv(cache_path)

    geo_lookup = cache_after.lazy().select(["LONGITUDE", "LATITUDE", *GEO_COLUMNS])
    (
        spine.join(geo_lookup, on=["LONGITUDE", "LATITUDE"], how="left")
        .sink_parquet(out_parquet)
    )
    if out_csv is not None:
        pl.scan_parquet(out_parquet).sink_csv(out_csv)

    match_counts_df = cache_after.group_by("CENSUS_MATCH_STATUS").agg(pl.len().alias("n"))
    summary = {
        "year": year,
        "input_path": str(spine_path),
        "output_parquet": str(out_parquet),
        "output_csv": str(out_csv) if out_csv is not None else None,
        "coord_cache_path": str(cache_path),
        "seeded_from_legacy_caches": seeded_cache_paths,
        "benchmark": BENCHMARK,
        "vintage": VINTAGE,
        "total_input_rows": total_rows,
        "rows_with_coords": rows_with_coords,
        "unique_coords": unique_coords.height,
        "cached_before": cache_before.height,
        "geocoded_now": len(new_cache_rows),
        "cache_rows_after": cache_after.height,
        "geocoder_match_counts": dict(
            zip(
                match_counts_df["CENSUS_MATCH_STATUS"].to_list(),
                match_counts_df["n"].to_list(),
            )
        ),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
