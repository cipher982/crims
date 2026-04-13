#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


BORO_MAP = {
    "M": "MANHATTAN",
    "B": "BRONX",
    "K": "BROOKLYN",
    "Q": "QUEENS",
    "S": "STATEN ISLAND",
}

ARREST_SCHEMA_OVERRIDES = {
    "ARREST_KEY": pl.Utf8,
    "ARREST_DATE": pl.Utf8,
    "PD_CD": pl.Utf8,
    "PD_DESC": pl.Utf8,
    "KY_CD": pl.Utf8,
    "OFNS_DESC": pl.Utf8,
    "LAW_CAT_CD": pl.Utf8,
    "ARREST_BORO": pl.Utf8,
    "ARREST_PRECINCT": pl.Utf8,
    "AGE_GROUP": pl.Utf8,
    "PERP_SEX": pl.Utf8,
    "PERP_RACE": pl.Utf8,
    "X_COORD_CD": pl.Utf8,
    "Y_COORD_CD": pl.Utf8,
    "Latitude": pl.Utf8,
    "Longitude": pl.Utf8,
}

COMPLAINT_SCHEMA_OVERRIDES = {
    "cmplnt_num": pl.Utf8,
    "cmplnt_fr_dt": pl.Utf8,
    "addr_pct_cd": pl.Utf8,
    "boro_nm": pl.Utf8,
    "pd_cd": pl.Utf8,
    "ky_cd": pl.Utf8,
    "ofns_desc": pl.Utf8,
    "law_cat_cd": pl.Utf8,
    "susp_age_group": pl.Utf8,
    "susp_sex": pl.Utf8,
    "susp_race": pl.Utf8,
    "latitude": pl.Utf8,
    "longitude": pl.Utf8,
}


def clean_upper(col: str) -> pl.Expr:
    return (
        pl.col(col)
        .cast(pl.Utf8)
        .str.strip_chars()
        .str.to_uppercase()
        .replace(["", "(NULL)", "UNKNOWN", "U"], [None, None, None, None])
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--write-csv", action="store_true")
    args = parser.parse_args()

    year = args.year
    raw_arrests = Path("data/raw/nypd_arrests_historic.csv")
    raw_complaints = Path(f"data/raw/nypd_complaints_{year}_minimal.csv")
    out_parquet = Path(f"data/derived/nypd_arrests_{year}_research_dataset.parquet")
    out_csv = Path(f"data/derived/nypd_arrests_{year}_research_dataset_polars.csv") if args.write_csv else None
    summary_path = Path(f"data/meta/nypd_arrests_{year}_research_dataset_polars_summary.json")

    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    boro_expr = (
        pl.when(pl.col("ARREST_BORO") == "M")
        .then(pl.lit("MANHATTAN"))
        .when(pl.col("ARREST_BORO") == "B")
        .then(pl.lit("BRONX"))
        .when(pl.col("ARREST_BORO") == "K")
        .then(pl.lit("BROOKLYN"))
        .when(pl.col("ARREST_BORO") == "Q")
        .then(pl.lit("QUEENS"))
        .when(pl.col("ARREST_BORO") == "S")
        .then(pl.lit("STATEN ISLAND"))
        .otherwise(None)
    )

    arrests = (
        pl.scan_csv(raw_arrests, schema_overrides=ARREST_SCHEMA_OVERRIDES)
        .with_columns(
            pl.col("ARREST_DATE").str.strptime(pl.Date, format="%m/%d/%Y").alias("ARREST_DATE_DT"),
            clean_upper("ARREST_PRECINCT").alias("ARREST_PRECINCT_CLEAN"),
            clean_upper("KY_CD").alias("KY_CD_CLEAN"),
            clean_upper("AGE_GROUP").alias("AGE_GROUP_CLEAN"),
            clean_upper("PERP_SEX").alias("PERP_SEX_CLEAN"),
            clean_upper("PERP_RACE").alias("PERP_RACE_CLEAN"),
            clean_upper("LAW_CAT_CD").alias("LAW_CAT_CD_CLEAN"),
            boro_expr.alias("ARREST_BORO_NM"),
        )
        .filter(pl.col("ARREST_DATE_DT").dt.year() == year)
    )

    complaints = (
        pl.scan_csv(raw_complaints, schema_overrides=COMPLAINT_SCHEMA_OVERRIDES)
        .with_columns(
            pl.col("cmplnt_fr_dt").str.slice(0, 10).str.strptime(pl.Date, format="%Y-%m-%d").alias("CMPLNT_DATE_DT"),
            clean_upper("addr_pct_cd").alias("ADDR_PCT_CD_CLEAN"),
            clean_upper("ky_cd").alias("KY_CD_CLEAN"),
            clean_upper("boro_nm").alias("BORO_NM_CLEAN"),
            clean_upper("susp_age_group").alias("SUSP_AGE_GROUP_CLEAN"),
            clean_upper("susp_sex").alias("SUSP_SEX_CLEAN"),
            clean_upper("susp_race").alias("SUSP_RACE_CLEAN"),
        )
    )

    join_keys_left = ["ARREST_DATE_DT", "ARREST_PRECINCT_CLEAN", "KY_CD_CLEAN", "ARREST_BORO_NM"]
    join_keys_right = ["CMPLNT_DATE_DT", "ADDR_PCT_CD_CLEAN", "KY_CD_CLEAN", "BORO_NM_CLEAN"]

    base_join = arrests.join(
        complaints,
        left_on=join_keys_left,
        right_on=join_keys_right,
        how="left",
    )

    base_agg = (
        base_join.group_by("ARREST_KEY")
        .agg(
            pl.col("cmplnt_num").drop_nulls().len().alias("COMPLAINT_BASE_COUNT"),
            pl.col("cmplnt_num").drop_nulls().first().alias("BASE_FIRST_CMPLNT_NUM"),
            pl.col("ofns_desc").drop_nulls().first().alias("BASE_FIRST_OFNS_DESC"),
        )
    )

    demo_join = base_join.filter(
        (
            pl.col("PERP_SEX_CLEAN").is_null()
            | pl.col("SUSP_SEX_CLEAN").is_null()
            | (pl.col("SUSP_SEX_CLEAN") == pl.col("PERP_SEX_CLEAN"))
        )
        & (
            pl.col("PERP_RACE_CLEAN").is_null()
            | pl.col("SUSP_RACE_CLEAN").is_null()
            | (pl.col("SUSP_RACE_CLEAN") == pl.col("PERP_RACE_CLEAN"))
        )
        & (
            pl.col("AGE_GROUP_CLEAN").is_null()
            | pl.col("SUSP_AGE_GROUP_CLEAN").is_null()
            | (pl.col("SUSP_AGE_GROUP_CLEAN") == pl.col("AGE_GROUP_CLEAN"))
        )
    )

    demo_agg = (
        demo_join.group_by("ARREST_KEY")
        .agg(
            pl.col("cmplnt_num").drop_nulls().len().alias("COMPLAINT_DEMO_COUNT"),
            pl.col("cmplnt_num").drop_nulls().first().alias("DEMO_FIRST_CMPLNT_NUM"),
            pl.col("ofns_desc").drop_nulls().first().alias("DEMO_FIRST_OFNS_DESC"),
            pl.col("law_cat_cd").drop_nulls().first().alias("DEMO_FIRST_LAW_CAT_CD"),
        )
    )

    result = (
        arrests.join(base_agg, on="ARREST_KEY", how="left")
        .join(demo_agg, on="ARREST_KEY", how="left")
        .with_columns(
            pl.col("COMPLAINT_BASE_COUNT").fill_null(0),
            pl.col("COMPLAINT_DEMO_COUNT").fill_null(0),
        )
        .with_columns(
            pl.when(pl.col("COMPLAINT_DEMO_COUNT") == 1)
            .then(pl.lit("unique_demo"))
            .when(pl.col("COMPLAINT_DEMO_COUNT") > 1)
            .then(pl.lit("ambiguous_demo"))
            .when(pl.col("COMPLAINT_BASE_COUNT") == 1)
            .then(pl.lit("unique_base"))
            .when(pl.col("COMPLAINT_BASE_COUNT") > 1)
            .then(pl.lit("ambiguous_base"))
            .otherwise(pl.lit("none"))
            .alias("COMPLAINT_MATCH_STATUS")
        )
        .select(
            "ARREST_KEY",
            "ARREST_DATE",
            "ARREST_BORO",
            "ARREST_BORO_NM",
            "ARREST_PRECINCT",
            "X_COORD_CD",
            "Y_COORD_CD",
            "Latitude",
            "Longitude",
            "PD_CD",
            "PD_DESC",
            "KY_CD",
            "OFNS_DESC",
            "LAW_CAT_CD",
            "AGE_GROUP",
            "PERP_SEX",
            "PERP_RACE",
            "COMPLAINT_BASE_COUNT",
            "COMPLAINT_DEMO_COUNT",
            "COMPLAINT_MATCH_STATUS",
            pl.when(pl.col("COMPLAINT_BASE_COUNT") == 1).then(pl.col("BASE_FIRST_CMPLNT_NUM")).otherwise(None).alias("UNIQUE_BASE_CMPLNT_NUM"),
            pl.when(pl.col("COMPLAINT_BASE_COUNT") == 1).then(pl.col("BASE_FIRST_OFNS_DESC")).otherwise(None).alias("UNIQUE_BASE_COMPLAINT_OFNS_DESC"),
            pl.when(pl.col("COMPLAINT_DEMO_COUNT") == 1).then(pl.col("DEMO_FIRST_CMPLNT_NUM")).otherwise(None).alias("UNIQUE_DEMO_CMPLNT_NUM"),
            pl.when(pl.col("COMPLAINT_DEMO_COUNT") == 1).then(pl.col("DEMO_FIRST_OFNS_DESC")).otherwise(None).alias("UNIQUE_DEMO_COMPLAINT_OFNS_DESC"),
            pl.when(pl.col("COMPLAINT_DEMO_COUNT") == 1).then(pl.col("DEMO_FIRST_LAW_CAT_CD")).otherwise(None).alias("UNIQUE_DEMO_COMPLAINT_LAW_CAT_CD"),
        )
    )

    result.sink_parquet(out_parquet)

    status_counts = (
        pl.scan_parquet(out_parquet)
        .group_by("COMPLAINT_MATCH_STATUS")
        .agg(pl.len().alias("n"))
        .collect()
        .to_dict(as_series=False)
    )
    status_counts = dict(zip(status_counts["COMPLAINT_MATCH_STATUS"], status_counts["n"]))

    if out_csv is not None:
        pl.scan_parquet(out_parquet).sink_csv(out_csv)

    summary = {
        "year": year,
        "output_parquet": str(out_parquet),
        "output_csv": str(out_csv) if out_csv is not None else None,
        "rows_written": int(pl.scan_parquet(out_parquet).select(pl.len()).collect().item()),
        "status_counts": status_counts,
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
