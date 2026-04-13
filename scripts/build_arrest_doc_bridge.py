#!/usr/bin/env python3
"""Build heuristic bridge between NYPD arrests and NYC DOC admissions.

Join strategy:
  1. Parse NYPD LAW_CODE (PL XXXYYZZZ) → penal code (XXX.YY) to match DOC TOP_CHARGE
  2. Match on: arrest_date == admit_date, sex, penal code
  3. Tighten with imputed age group from DOC birth year
  4. Keep only unique 1:1 matches (one arrest ↔ one admission)

This is a *candidate* bridge — not ground truth. The match is labeled explicitly
and only unique matches are kept to maximize precision.

Outputs:
  data/derived/arrest_doc_bridge.parquet       — matched arrest-admission pairs
  data/derived/arrest_doc_bridge_episodes.parquet — repeat linked episodes for people with 2+
  data/meta/arrest_doc_bridge_summary.json     — match quality metrics
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl


RAW_DIR = Path("data/raw")
DERIVED_DIR = Path("data/derived")
META_DIR = Path("data/meta")


def parse_law_code_to_penal(law_code: pl.Expr) -> pl.Expr:
    """Convert NYPD LAW_CODE (e.g. 'PL 1552500') to penal code (e.g. '155.25').

    Format: PL XXXYYZZZ → XXX.YY
    - Strip 'PL ' prefix
    - Take first 3 digits as section
    - Take next 2 digits as subsection
    - Drop trailing ZZZ (sub-subsection)
    """
    numeric = law_code.str.replace(r"^PL\s*", "")
    section = numeric.str.slice(0, 3).str.strip_chars_start("0")
    subsection = numeric.str.slice(3, 2)
    return (section + "." + subsection).alias("penal_code")


def age_group_from_birth_year(birth_year: pl.Expr, ref_year: pl.Expr) -> pl.Expr:
    """Map DOC imputed age at admission to NYPD-style age bucket."""
    age = ref_year - birth_year
    return (
        pl.when(age < 18).then(pl.lit("<18"))
        .when(age < 25).then(pl.lit("18-24"))
        .when(age < 45).then(pl.lit("25-44"))
        .when(age < 65).then(pl.lit("45-64"))
        .when(age.is_not_null()).then(pl.lit("65+"))
        .otherwise(None)
    )


def load_arrests() -> pl.DataFrame:
    """Load NYPD arrests with parsed penal code."""
    return (
        pl.scan_csv(RAW_DIR / "nypd_arrests_historic.csv", infer_schema_length=10000, ignore_errors=True)
        .select(
            pl.col("ARREST_KEY").cast(pl.Utf8),
            pl.col("ARREST_DATE").str.slice(0, 10).str.to_date("%m/%d/%Y").alias("arrest_date"),
            parse_law_code_to_penal(pl.col("LAW_CODE")),
            pl.col("LAW_CAT_CD").str.strip_chars().alias("law_category"),
            pl.col("PERP_SEX").str.strip_chars().alias("arrest_sex"),
            pl.col("AGE_GROUP").str.strip_chars().alias("arrest_age_group"),
            pl.col("PERP_RACE").str.strip_chars().alias("arrest_race"),
            pl.col("ARREST_BORO").str.strip_chars().alias("arrest_boro"),
            pl.col("ARREST_PRECINCT").cast(pl.Int32, strict=False).alias("arrest_precinct"),
            pl.col("Latitude").cast(pl.Float64, strict=False).alias("lat"),
            pl.col("Longitude").cast(pl.Float64, strict=False).alias("lon"),
        )
        .filter(pl.col("penal_code").is_not_null() & (pl.col("penal_code") != "."))
        .collect()
    )


def load_doc_admissions() -> pl.DataFrame:
    """Load DOC admissions with birth year from recidivism episodes."""
    episodes = pl.read_parquet(DERIVED_DIR / "doc_recidivism_episodes.parquet")
    return episodes.select(
        "INMATEID",
        pl.col("admit_date"),
        pl.col("discharge_date"),
        pl.col("top_charge"),
        pl.col("sex").alias("doc_sex"),
        pl.col("race").alias("doc_race"),
        pl.col("approx_birth_year"),
        pl.col("stay_days"),
        pl.col("episode_num"),
        pl.col("total_episodes"),
        pl.col("status_code"),
    )


def sex_map_doc_to_nypd(doc_sex: pl.Expr) -> pl.Expr:
    """Map DOC sex codes to NYPD codes."""
    return doc_sex.replace_strict({"M": "M", "F": "F"}, default=None)


def build_bridge(arrests: pl.DataFrame, doc: pl.DataFrame) -> pl.DataFrame:
    """Match arrests to DOC admissions on date + sex + penal code + age group."""

    # Normalize DOC sex to NYPD format
    doc = doc.with_columns(sex_map_doc_to_nypd(pl.col("doc_sex")).alias("match_sex"))

    # Compute expected NYPD age group at admission
    doc = doc.with_columns(
        age_group_from_birth_year(
            pl.col("approx_birth_year"),
            pl.col("admit_date").dt.year(),
        ).alias("expected_age_group"),
    )

    # Join on date + sex + penal code
    matched = arrests.join(
        doc,
        left_on=["arrest_date", "arrest_sex", "penal_code"],
        right_on=["admit_date", "match_sex", "top_charge"],
        how="inner",
    )

    # Tighten: filter to rows where age group matches (when both are known)
    matched = matched.filter(
        pl.col("expected_age_group").is_null()
        | pl.col("arrest_age_group").is_null()
        | ~pl.col("arrest_age_group").is_in(["<18", "18-24", "25-44", "45-64", "65+"])
        | (pl.col("arrest_age_group") == pl.col("expected_age_group"))
    )

    return matched


def deduplicate_to_unique(matched: pl.DataFrame) -> pl.DataFrame:
    """Keep only 1:1 matches — each arrest maps to exactly one admission and vice versa."""

    # Count matches per arrest
    arrest_counts = (
        matched.group_by("ARREST_KEY")
        .len()
        .filter(pl.col("len") == 1)
        .select("ARREST_KEY")
    )

    # Count matches per DOC admission (INMATEID + arrest_date as proxy for admit_date)
    doc_key_counts = (
        matched.group_by(["INMATEID", "arrest_date"])
        .len()
        .filter(pl.col("len") == 1)
        .select(["INMATEID", "arrest_date"])
    )

    # Inner join to keep only rows that are unique on both sides
    unique = matched.join(arrest_counts, on="ARREST_KEY", how="semi")
    unique = unique.join(doc_key_counts, on=["INMATEID", "arrest_date"], how="semi")

    return unique


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading arrests...")
    arrests = load_arrests()
    print(f"  {arrests.height:,} arrests with parseable penal codes")

    print("Loading DOC admissions...")
    doc = load_doc_admissions()
    doc_eligible = doc.filter(pl.col("top_charge").is_not_null())
    print(f"  {doc.height:,} total admissions, {doc_eligible.height:,} with TOP_CHARGE")

    print("Matching on date + sex + penal code + age group...")
    matched = build_bridge(arrests, doc)
    print(f"  {matched.height:,} raw matches")

    print("Deduplicating to unique 1:1 matches...")
    bridge = deduplicate_to_unique(matched)
    print(f"  {bridge.height:,} unique matched pairs")

    unique_people = bridge.select("INMATEID").n_unique()
    repeat_people = (
        bridge.group_by("INMATEID")
        .len()
        .filter(pl.col("len") > 1)
        .height
    )
    print(f"  {unique_people:,} unique people, {repeat_people:,} with 2+ linked episodes")

    # Build repeat-episode dataset
    repeat_ids = (
        bridge.group_by("INMATEID").len().filter(pl.col("len") > 1).select("INMATEID")
    )
    repeat_episodes = bridge.join(repeat_ids, on="INMATEID", how="semi").sort(
        ["INMATEID", "arrest_date"]
    )

    # Summary stats
    boro_dist = [
        {"boro": r["arrest_boro"], "count": r["len"]}
        for r in bridge.group_by("arrest_boro")
        .len()
        .sort("len", descending=True)
        .iter_rows(named=True)
    ]

    top_charges = [
        {"charge": r["penal_code"], "count": r["len"]}
        for r in bridge.group_by("penal_code")
        .len()
        .sort("len", descending=True)
        .head(15)
        .iter_rows(named=True)
    ]

    summary = {
        "total_arrests_with_penal_code": arrests.height,
        "doc_admissions_with_charge": doc_eligible.height,
        "raw_matches": matched.height,
        "unique_1to1_matches": bridge.height,
        "match_rate_of_eligible_doc": round(bridge.height / doc_eligible.height, 4)
        if doc_eligible.height
        else 0,
        "unique_people": unique_people,
        "people_with_repeat_linked_episodes": repeat_people,
        "repeat_linked_episodes": repeat_episodes.height,
        "borough_distribution": boro_dist,
        "top_matched_charges": top_charges,
    }

    # Write outputs
    bridge_path = DERIVED_DIR / "arrest_doc_bridge.parquet"
    episodes_path = DERIVED_DIR / "arrest_doc_bridge_episodes.parquet"
    summary_path = META_DIR / "arrest_doc_bridge_summary.json"

    bridge.write_parquet(bridge_path)
    repeat_episodes.write_parquet(episodes_path)
    summary_path.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    print(f"\nWrote {bridge_path} ({bridge.height:,} rows)")
    print(f"Wrote {episodes_path} ({repeat_episodes.height:,} rows)")
    print(f"Wrote {summary_path}")
    print()
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
