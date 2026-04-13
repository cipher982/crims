#!/usr/bin/env python3
"""Time-bounded cohort recidivism rates for NYC DOC.

For each discharge year cohort, computes what share of released people returned
to jail within 1 year, 2 years, and 3 years. This produces rates directly
comparable to BJS and published recidivism studies.

Also breaks down by demographics, charge type, and age group.

Outputs:
  data/derived/doc_cohort_recidivism.parquet  — one row per person-cohort with outcomes
  data/meta/doc_cohort_recidivism_summary.json — aggregate rates by year and demographic
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl


DERIVED_DIR = Path("data/derived")
META_DIR = Path("data/meta")

# We need at least this many days of follow-up after discharge
WINDOWS = {
    "returned_1yr": 365,
    "returned_2yr": 730,
    "returned_3yr": 1095,
}


def load_episodes() -> pl.DataFrame:
    return pl.read_parquet(DERIVED_DIR / "doc_recidivism_episodes.parquet")


def build_cohort_table(episodes: pl.DataFrame) -> pl.DataFrame:
    """For each person's each discharge, determine if/when they returned.

    A person can appear in multiple cohorts (discharged in 2016 and again in 2018).
    We take the *first discharge per person per year* as the cohort entry point
    and look for any subsequent admission.
    """
    # Only episodes with a discharge date
    discharged = episodes.filter(pl.col("discharge_date").is_not_null()).sort(
        ["INMATEID", "discharge_date"]
    )

    # For each discharge, find the next admission date for that person
    # (already have this implicitly — the next episode's admit_date)
    discharged = discharged.with_columns(
        pl.col("admit_date").shift(-1).over("INMATEID").alias("next_admit_date"),
    )

    # Compute days to next admission
    discharged = discharged.with_columns(
        (pl.col("next_admit_date") - pl.col("discharge_date"))
        .dt.total_days()
        .alias("days_to_return"),
    )

    # Cohort year = year of discharge
    discharged = discharged.with_columns(
        pl.col("discharge_date").dt.year().alias("cohort_year"),
    )

    # Data end date for censoring: use the max admission date in the dataset
    data_end = episodes.select(pl.col("admit_date").max()).item()

    # Follow-up days available from discharge to end of data
    discharged = discharged.with_columns(
        (pl.lit(data_end) - pl.col("discharge_date"))
        .dt.total_days()
        .alias("followup_days"),
    )

    # Compute return flags for each window
    for label, days in WINDOWS.items():
        discharged = discharged.with_columns(
            pl.when(pl.col("followup_days") < days)
            .then(None)  # censored — not enough follow-up
            .when(pl.col("days_to_return").is_not_null() & (pl.col("days_to_return") <= days))
            .then(True)
            .otherwise(False)
            .alias(label),
        )

    # Age group at discharge
    discharged = discharged.with_columns(
        pl.when(pl.col("age_at_discharge") < 18).then(pl.lit("Under 18"))
        .when(pl.col("age_at_discharge") <= 25).then(pl.lit("18-25"))
        .when(pl.col("age_at_discharge") <= 35).then(pl.lit("26-35"))
        .when(pl.col("age_at_discharge") <= 50).then(pl.lit("36-50"))
        .when(pl.col("age_at_discharge").is_not_null()).then(pl.lit("51+"))
        .otherwise(pl.lit("Unknown"))
        .alias("age_group"),
    )

    # Charge category (broad grouping of top penal law sections)
    discharged = discharged.with_columns(
        pl.when(pl.col("top_charge").is_null()).then(pl.lit("Unknown"))
        .when(pl.col("top_charge").str.starts_with("120")).then(pl.lit("Assault"))
        .when(pl.col("top_charge").str.starts_with("125")).then(pl.lit("Homicide"))
        .when(pl.col("top_charge").str.starts_with("130")).then(pl.lit("Sex Offense"))
        .when(pl.col("top_charge").str.starts_with("140")).then(pl.lit("Burglary"))
        .when(pl.col("top_charge").str.starts_with("155")).then(pl.lit("Larceny"))
        .when(pl.col("top_charge").str.starts_with("160")).then(pl.lit("Robbery"))
        .when(pl.col("top_charge").str.starts_with("220")).then(pl.lit("Drug"))
        .when(pl.col("top_charge").str.starts_with("221")).then(pl.lit("Marijuana"))
        .when(pl.col("top_charge").str.starts_with("265")).then(pl.lit("Weapon"))
        .when(pl.col("top_charge").str.starts_with("215")).then(pl.lit("Contempt/Bail Jump"))
        .otherwise(pl.lit("Other"))
        .alias("charge_category"),
    )

    return discharged


def compute_rates(
    cohort: pl.DataFrame,
    group_cols: list[str],
    window: str,
    min_n: int = 50,
) -> list[dict]:
    """Compute recidivism rate for a given window, grouped by columns."""
    eligible = cohort.filter(pl.col(window).is_not_null())
    if eligible.height == 0:
        return []

    grouped = (
        eligible.group_by(group_cols)
        .agg(
            pl.len().alias("n"),
            pl.col(window).sum().alias("returned"),
        )
        .filter(pl.col("n") >= min_n)
        .with_columns(
            (pl.col("returned") / pl.col("n")).round(4).alias("rate"),
        )
        .sort(group_cols)
    )

    return [row for row in grouped.iter_rows(named=True)]


def build_summary(cohort: pl.DataFrame) -> dict:
    """Build comprehensive summary with rates by year, demographics, charges."""
    summary = {}

    # Overall rates by cohort year
    for window_label, window_days in WINDOWS.items():
        rates = compute_rates(cohort, ["cohort_year"], window_label, min_n=100)
        summary[f"{window_label}_by_year"] = rates

    # 1-year rate by demographics
    summary["returned_1yr_by_race"] = compute_rates(cohort, ["cohort_year", "race"], "returned_1yr", min_n=50)
    summary["returned_1yr_by_sex"] = compute_rates(cohort, ["cohort_year", "sex"], "returned_1yr", min_n=50)
    summary["returned_1yr_by_age_group"] = compute_rates(cohort, ["cohort_year", "age_group"], "returned_1yr", min_n=50)
    summary["returned_1yr_by_charge"] = compute_rates(cohort, ["cohort_year", "charge_category"], "returned_1yr", min_n=50)

    # Overall aggregate rates (all years pooled)
    for window_label in WINDOWS:
        eligible = cohort.filter(pl.col(window_label).is_not_null())
        if eligible.height > 0:
            returned = eligible.select(pl.col(window_label).sum()).item()
            total = eligible.height
            summary[f"{window_label}_overall"] = {
                "n": total,
                "returned": returned,
                "rate": round(returned / total, 4),
            }

    # Median days to return for those who did return, by year
    returners = cohort.filter(
        pl.col("days_to_return").is_not_null() & (pl.col("days_to_return") > 0)
    )
    median_by_year = (
        returners.group_by(
            pl.col("discharge_date").dt.year().alias("cohort_year")
        )
        .agg(
            pl.col("days_to_return").median().alias("median_days_to_return"),
            pl.col("days_to_return").mean().round(1).alias("mean_days_to_return"),
            pl.len().alias("n_returned"),
        )
        .sort("cohort_year")
    )
    summary["days_to_return_by_year"] = [
        row for row in median_by_year.iter_rows(named=True)
    ]

    return summary


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading episodes...")
    episodes = load_episodes()
    print(f"  {episodes.height:,} episodes, {episodes.select('INMATEID').n_unique():,} people")

    print("Building cohort table...")
    cohort = build_cohort_table(episodes)

    # Report coverage
    for label, days in WINDOWS.items():
        eligible = cohort.filter(pl.col(label).is_not_null())
        returned = eligible.filter(pl.col(label) == True)  # noqa: E712
        print(
            f"  {label}: {eligible.height:,} eligible discharges, "
            f"{returned.height:,} returned ({returned.height / eligible.height:.1%})"
        )

    print("Computing summary rates...")
    summary = build_summary(cohort)

    # Write outputs
    cohort_path = DERIVED_DIR / "doc_cohort_recidivism.parquet"
    summary_path = META_DIR / "doc_cohort_recidivism_summary.json"

    cohort.write_parquet(cohort_path)
    summary_path.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    print(f"\nWrote {cohort_path} ({cohort.height:,} rows)")
    print(f"Wrote {summary_path}")

    # Print key rates
    print("\n=== 1-Year Return Rates by Cohort Year ===")
    for r in summary.get("returned_1yr_by_year", []):
        print(f"  {r['cohort_year']}: {r['rate']:.1%}  (n={r['n']:,})")

    print("\n=== Overall Rates ===")
    for label in WINDOWS:
        o = summary.get(f"{label}_overall", {})
        if o:
            print(f"  {label}: {o['rate']:.1%}  (n={o['n']:,})")

    print("\n=== 1-Year Rate by Charge Category (2018 cohort) ===")
    for r in summary.get("returned_1yr_by_charge", []):
        if r["cohort_year"] == 2018:
            print(f"  {r['charge_category']:20s} {r['rate']:.1%}  (n={r['n']:,})")


if __name__ == "__main__":
    main()
