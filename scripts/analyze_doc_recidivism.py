#!/usr/bin/env python3
"""Analyze DOC recidivism patterns using INMATEID as a persistent person identifier.

Reads raw DOC admissions + discharges, builds per-person episode histories,
and computes recidivism metrics: return rates, time-to-return, charge patterns,
and demographic breakdowns.

Outputs:
  data/derived/doc_recidivism_persons.parquet   — one row per person with summary stats
  data/derived/doc_recidivism_episodes.parquet  — one row per admission with episode context
  data/meta/doc_recidivism_summary.json         — aggregate metrics
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl


RAW_DIR = Path("data/raw")
DERIVED_DIR = Path("data/derived")
META_DIR = Path("data/meta")


def load_admissions() -> pl.DataFrame:
    return (
        pl.scan_csv(RAW_DIR / "doc_inmate_admissions.csv")
        .select(
            pl.col("INMATEID").cast(pl.Utf8),
            pl.col("ADMITTED_DT").str.slice(0, 10).str.to_date("%m/%d/%Y").alias("admit_date"),
            pl.col("RACE").str.strip_chars().alias("race"),
            pl.col("GENDER").str.strip_chars().alias("sex"),
            pl.col("INMATE_STATUS_CODE").str.strip_chars().alias("status_code"),
            pl.col("TOP_CHARGE").str.strip_chars().alias("top_charge"),
        )
        .collect()
    )


def load_discharges() -> pl.DataFrame:
    return (
        pl.scan_csv(RAW_DIR / "doc_inmate_discharges.csv")
        .select(
            pl.col("INMATEID").cast(pl.Utf8),
            pl.col("ADMITTED_DT").str.slice(0, 10).str.to_date("%m/%d/%Y").alias("admit_date"),
            pl.col("DISCHARGED_DT").str.slice(0, 10).str.to_date("%m/%d/%Y").alias("discharge_date"),
            pl.col("AGE").cast(pl.Int32).alias("age_at_discharge"),
        )
        .collect()
    )


def build_episodes(adm: pl.DataFrame, dis: pl.DataFrame) -> pl.DataFrame:
    """Join admissions to discharges and compute per-person episode sequences."""
    # Best discharge match per admission: INMATEID + admit_date, take first
    dis_dedup = dis.sort(["INMATEID", "admit_date", "discharge_date"]).unique(
        subset=["INMATEID", "admit_date"], keep="first"
    )

    episodes = adm.join(dis_dedup, on=["INMATEID", "admit_date"], how="left")

    # Compute stay duration
    episodes = episodes.with_columns(
        (pl.col("discharge_date") - pl.col("admit_date")).dt.total_days().alias("stay_days")
    )

    # Sort and add episode numbering per person
    episodes = (
        episodes.sort(["INMATEID", "admit_date"])
        .with_columns(
            pl.col("admit_date").rank("ordinal").over("INMATEID").cast(pl.Int32).alias("episode_num"),
            pl.len().over("INMATEID").cast(pl.Int32).alias("total_episodes"),
        )
    )

    # Compute gap from previous discharge to this admission
    episodes = episodes.with_columns(
        pl.col("discharge_date").shift(1).over("INMATEID").alias("prev_discharge_date")
    ).with_columns(
        (pl.col("admit_date") - pl.col("prev_discharge_date")).dt.total_days().alias("gap_days")
    )

    # Impute birth year from discharge age
    episodes = episodes.with_columns(
        (pl.col("discharge_date").dt.year() - pl.col("age_at_discharge")).alias("approx_birth_year")
    )

    return episodes


def build_persons(episodes: pl.DataFrame) -> pl.DataFrame:
    """Aggregate episodes to one row per person."""
    return episodes.group_by("INMATEID").agg(
        pl.len().alias("total_admissions"),
        pl.col("admit_date").min().alias("first_admission"),
        pl.col("admit_date").max().alias("last_admission"),
        pl.col("discharge_date").max().alias("last_discharge"),
        pl.col("stay_days").mean().alias("avg_stay_days"),
        pl.col("stay_days").median().alias("median_stay_days"),
        pl.col("gap_days").filter(pl.col("gap_days").is_not_null()).mean().alias("avg_gap_days"),
        pl.col("gap_days").filter(pl.col("gap_days").is_not_null()).median().alias("median_gap_days"),
        pl.col("race").first().alias("race"),
        pl.col("sex").first().alias("sex"),
        pl.col("approx_birth_year").median().cast(pl.Int32).alias("approx_birth_year"),
        pl.col("top_charge").drop_nulls().first().alias("first_known_charge"),
        pl.col("top_charge").drop_nulls().last().alias("last_known_charge"),
        pl.col("top_charge").drop_nulls().n_unique().alias("distinct_charges"),
    ).with_columns(
        pl.when(pl.col("total_admissions") == 1).then(pl.lit("single"))
        .when(pl.col("total_admissions") <= 3).then(pl.lit("low_repeat"))
        .when(pl.col("total_admissions") <= 10).then(pl.lit("moderate_repeat"))
        .otherwise(pl.lit("high_repeat"))
        .alias("recidivism_tier"),
    )


def compute_summary(persons: pl.DataFrame, episodes: pl.DataFrame) -> dict:
    """Build aggregate summary metrics."""
    total_people = persons.height
    repeaters = persons.filter(pl.col("total_admissions") > 1)
    repeat_count = repeaters.height

    # Readmission gap buckets
    gaps = episodes.filter(pl.col("gap_days").is_not_null()).select("gap_days")
    gap_buckets = (
        gaps.with_columns(
            pl.when(pl.col("gap_days") <= 7).then(pl.lit("0-7d"))
            .when(pl.col("gap_days") <= 30).then(pl.lit("8-30d"))
            .when(pl.col("gap_days") <= 90).then(pl.lit("31-90d"))
            .when(pl.col("gap_days") <= 180).then(pl.lit("91-180d"))
            .when(pl.col("gap_days") <= 365).then(pl.lit("181-365d"))
            .when(pl.col("gap_days") <= 730).then(pl.lit("1-2yr"))
            .otherwise(pl.lit("2yr+"))
            .alias("bucket")
        )
        .group_by("bucket")
        .len()
        .sort("bucket")
    )

    # Recidivism tier breakdown
    tier_counts = persons.group_by("recidivism_tier").len().sort("recidivism_tier")

    # Demographics of repeaters vs non-repeaters
    demo_by_tier = (
        persons.group_by(["recidivism_tier", "race", "sex"])
        .len()
        .sort(["recidivism_tier", "len"], descending=[False, True])
    )

    # Charge changes for repeaters with 2+ known charges
    charge_changers = persons.filter(
        (pl.col("distinct_charges") > 1) & (pl.col("total_admissions") > 1)
    )

    return {
        "total_unique_people": total_people,
        "people_single_admission": total_people - repeat_count,
        "people_repeat_admission": repeat_count,
        "repeat_rate": round(repeat_count / total_people, 4) if total_people else 0,
        "admission_count_percentiles": {
            "p50": persons.select(pl.col("total_admissions").median()).item(),
            "p75": persons.select(pl.col("total_admissions").quantile(0.75)).item(),
            "p90": persons.select(pl.col("total_admissions").quantile(0.90)).item(),
            "p99": persons.select(pl.col("total_admissions").quantile(0.99)).item(),
            "max": persons.select(pl.col("total_admissions").max()).item(),
        },
        "readmission_gap_days": {
            "mean": round(gaps.select(pl.col("gap_days").mean()).item(), 1),
            "median": round(gaps.select(pl.col("gap_days").median()).item(), 1),
            "p25": round(gaps.select(pl.col("gap_days").quantile(0.25)).item(), 1),
            "p75": round(gaps.select(pl.col("gap_days").quantile(0.75)).item(), 1),
        },
        "readmission_gap_buckets": [
            {"bucket": r["bucket"], "count": r["len"]}
            for r in gap_buckets.iter_rows(named=True)
        ],
        "recidivism_tiers": [
            {"tier": r["recidivism_tier"], "count": r["len"]}
            for r in tier_counts.iter_rows(named=True)
        ],
        "people_with_charge_changes": charge_changers.height,
        "top_first_charges_repeaters": [
            {"charge": r["first_known_charge"], "count": r["len"]}
            for r in repeaters.filter(pl.col("first_known_charge").is_not_null())
            .group_by("first_known_charge")
            .len()
            .sort("len", descending=True)
            .head(15)
            .iter_rows(named=True)
        ],
    }


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading raw data...")
    adm = load_admissions()
    dis = load_discharges()
    print(f"  Admissions: {adm.height:,}  Discharges: {dis.height:,}")

    print("Building episodes...")
    episodes = build_episodes(adm, dis)
    print(f"  Episodes: {episodes.height:,}  Unique people: {episodes.select('INMATEID').n_unique():,}")

    print("Building person summaries...")
    persons = build_persons(episodes)

    print("Computing summary metrics...")
    summary = compute_summary(persons, episodes)

    # Write outputs
    ep_path = DERIVED_DIR / "doc_recidivism_episodes.parquet"
    per_path = DERIVED_DIR / "doc_recidivism_persons.parquet"
    sum_path = META_DIR / "doc_recidivism_summary.json"

    episodes.write_parquet(ep_path)
    persons.write_parquet(per_path)
    sum_path.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    print(f"\nWrote {ep_path} ({episodes.height:,} rows)")
    print(f"Wrote {per_path} ({persons.height:,} rows)")
    print(f"Wrote {sum_path}")
    print()
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
