#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


SUMMONS_SCHEMA_OVERRIDES = {
    "SUMMONS_KEY": pl.Utf8,
    "SUMMONS_DATE": pl.Utf8,
    "OFFENSE_DESCRIPTION": pl.Utf8,
    "LAW_SECTION_NUMBER": pl.Utf8,
    "SUMMONS_CATEGORY_TYPE": pl.Utf8,
    "AGE_GROUP": pl.Utf8,
    "SEX": pl.Utf8,
    "RACE": pl.Utf8,
    "BORO": pl.Utf8,
    "PRECINCT_OF_OCCUR": pl.Utf8,
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

DOC_ADMISSIONS_SCHEMA_OVERRIDES = {
    "INMATEID": pl.Utf8,
    "ADMITTED_DT": pl.Utf8,
    "TOP_CHARGE": pl.Utf8,
    "GENDER": pl.Utf8,
    "RACE": pl.Utf8,
}

DOC_DISCHARGES_SCHEMA_OVERRIDES = {
    "INMATEID": pl.Utf8,
    "DISCHARGED_DT": pl.Utf8,
    "TOP_CHARGE": pl.Utf8,
    "GENDER": pl.Utf8,
    "RACE": pl.Utf8,
    "AGE": pl.Utf8,
}


FIELD_ORDER = [
    "EVENT_SOURCE",
    "EVENT_STAGE",
    "EVENT_KEY",
    "EVENT_DATE",
    "EVENT_YEAR",
    "BORO",
    "PRECINCT",
    "OFFENSE_CODE",
    "OFFENSE_DESC",
    "LAW_CATEGORY",
    "SEX",
    "RACE",
    "AGE_BUCKET",
    "AGE_VALUE",
    "LATITUDE",
    "LONGITUDE",
    "PUBLIC_PERSON_ID",
    "PUBLIC_PERSON_ID_TYPE",
    "RELATED_EVENT_KEY",
    "RELATED_EVENT_TYPE",
    "LINK_STATUS",
]


def ensure_columns(lf: pl.LazyFrame) -> pl.LazyFrame:
    missing = [col for col in FIELD_ORDER if col not in lf.collect_schema().names()]
    if missing:
        lf = lf.with_columns([pl.lit(None).alias(col) for col in missing])
    return lf.select(FIELD_ORDER)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    year = args.year

    arrests_parquet = Path(f"data/derived/nypd_arrests_{year}_research_dataset.parquet")
    complaints_csv = Path(f"data/raw/nypd_complaints_{year}_minimal.csv")
    summonses_csv = Path("data/raw/nypd_summonses_historic.csv")
    admissions_csv = Path("data/raw/doc_inmate_admissions.csv")
    discharges_csv = Path("data/raw/doc_inmate_discharges.csv")

    out_parquet = Path(f"data/derived/public_event_spine_{year}.parquet")
    out_csv = Path(f"data/derived/public_event_spine_{year}_polars.csv")
    summary_path = Path(f"data/meta/public_event_spine_{year}_polars_summary.json")
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    arrests = ensure_columns(
        pl.scan_parquet(arrests_parquet).select(
            pl.lit("nypd_arrests").alias("EVENT_SOURCE"),
            pl.lit("arrest").alias("EVENT_STAGE"),
            pl.col("ARREST_KEY").alias("EVENT_KEY"),
            pl.col("ARREST_DATE").str.strptime(pl.Date, format="%m/%d/%Y").dt.to_string().alias("EVENT_DATE"),
            pl.lit(str(year)).alias("EVENT_YEAR"),
            pl.col("ARREST_BORO_NM").alias("BORO"),
            pl.col("ARREST_PRECINCT").alias("PRECINCT"),
            pl.col("KY_CD").alias("OFFENSE_CODE"),
            pl.col("OFNS_DESC").alias("OFFENSE_DESC"),
            pl.col("LAW_CAT_CD").alias("LAW_CATEGORY"),
            pl.col("PERP_SEX").alias("SEX"),
            pl.col("PERP_RACE").alias("RACE"),
            pl.col("AGE_GROUP").alias("AGE_BUCKET"),
            pl.col("Latitude").alias("LATITUDE"),
            pl.col("Longitude").alias("LONGITUDE"),
            pl.coalesce(["UNIQUE_DEMO_CMPLNT_NUM", "UNIQUE_BASE_CMPLNT_NUM"]).alias("RELATED_EVENT_KEY"),
            pl.when(pl.coalesce(["UNIQUE_DEMO_CMPLNT_NUM", "UNIQUE_BASE_CMPLNT_NUM"]).is_not_null())
            .then(pl.lit("complaint"))
            .otherwise(None)
            .alias("RELATED_EVENT_TYPE"),
            pl.col("COMPLAINT_MATCH_STATUS").alias("LINK_STATUS"),
        )
    )

    complaints = ensure_columns(
        pl.scan_csv(complaints_csv, schema_overrides=COMPLAINT_SCHEMA_OVERRIDES)
        .with_columns(pl.col("cmplnt_fr_dt").str.slice(0, 10).alias("EVENT_DATE"))
        .select(
            pl.lit("nypd_complaints").alias("EVENT_SOURCE"),
            pl.lit("complaint").alias("EVENT_STAGE"),
            pl.col("cmplnt_num").alias("EVENT_KEY"),
            "EVENT_DATE",
            pl.lit(str(year)).alias("EVENT_YEAR"),
            pl.col("boro_nm").alias("BORO"),
            pl.col("addr_pct_cd").alias("PRECINCT"),
            pl.col("ky_cd").alias("OFFENSE_CODE"),
            pl.col("ofns_desc").alias("OFFENSE_DESC"),
            pl.col("law_cat_cd").alias("LAW_CATEGORY"),
            pl.col("susp_sex").alias("SEX"),
            pl.col("susp_race").alias("RACE"),
            pl.col("susp_age_group").alias("AGE_BUCKET"),
            pl.col("latitude").alias("LATITUDE"),
            pl.col("longitude").alias("LONGITUDE"),
        )
    )

    summonses = ensure_columns(
        pl.scan_csv(summonses_csv, schema_overrides=SUMMONS_SCHEMA_OVERRIDES)
        .with_columns(pl.col("SUMMONS_DATE").str.strptime(pl.Date, format="%m/%d/%Y").alias("SUMMONS_DATE_DT"))
        .filter(pl.col("SUMMONS_DATE_DT").dt.year() == year)
        .select(
            pl.lit("nypd_summonses").alias("EVENT_SOURCE"),
            pl.lit("summons").alias("EVENT_STAGE"),
            pl.col("SUMMONS_KEY").alias("EVENT_KEY"),
            pl.col("SUMMONS_DATE_DT").dt.to_string().alias("EVENT_DATE"),
            pl.lit(str(year)).alias("EVENT_YEAR"),
            pl.col("BORO").alias("BORO"),
            pl.col("PRECINCT_OF_OCCUR").alias("PRECINCT"),
            pl.col("LAW_SECTION_NUMBER").alias("OFFENSE_CODE"),
            pl.col("OFFENSE_DESCRIPTION").alias("OFFENSE_DESC"),
            pl.col("SUMMONS_CATEGORY_TYPE").alias("LAW_CATEGORY"),
            pl.col("SEX").alias("SEX"),
            pl.col("RACE").alias("RACE"),
            pl.col("AGE_GROUP").alias("AGE_BUCKET"),
            pl.col("Latitude").alias("LATITUDE"),
            pl.col("Longitude").alias("LONGITUDE"),
        )
    )

    admissions = ensure_columns(
        pl.scan_csv(admissions_csv, schema_overrides=DOC_ADMISSIONS_SCHEMA_OVERRIDES)
        .with_columns(pl.col("ADMITTED_DT").str.strptime(pl.Datetime, format="%m/%d/%Y %I:%M:%S %p").alias("ADMITTED_DT_TS"))
        .filter(pl.col("ADMITTED_DT_TS").dt.year() == year)
        .select(
            pl.lit("doc_admissions").alias("EVENT_SOURCE"),
            pl.lit("custody_admission").alias("EVENT_STAGE"),
            pl.concat_str(["INMATEID", "ADMITTED_DT"], separator="|").alias("EVENT_KEY"),
            pl.col("ADMITTED_DT_TS").dt.date().dt.to_string().alias("EVENT_DATE"),
            pl.lit(str(year)).alias("EVENT_YEAR"),
            pl.col("TOP_CHARGE").alias("OFFENSE_CODE"),
            pl.col("GENDER").alias("SEX"),
            pl.col("RACE").alias("RACE"),
            pl.col("INMATEID").alias("PUBLIC_PERSON_ID"),
            pl.lit("INMATEID").alias("PUBLIC_PERSON_ID_TYPE"),
        )
    )

    discharges = ensure_columns(
        pl.scan_csv(discharges_csv, schema_overrides=DOC_DISCHARGES_SCHEMA_OVERRIDES)
        .with_columns(pl.col("DISCHARGED_DT").str.strptime(pl.Datetime, format="%m/%d/%Y %I:%M:%S %p").alias("DISCHARGED_DT_TS"))
        .filter(pl.col("DISCHARGED_DT_TS").dt.year() == year)
        .select(
            pl.lit("doc_discharges").alias("EVENT_SOURCE"),
            pl.lit("custody_discharge").alias("EVENT_STAGE"),
            pl.concat_str(["INMATEID", "DISCHARGED_DT"], separator="|").alias("EVENT_KEY"),
            pl.col("DISCHARGED_DT_TS").dt.date().dt.to_string().alias("EVENT_DATE"),
            pl.lit(str(year)).alias("EVENT_YEAR"),
            pl.col("TOP_CHARGE").alias("OFFENSE_CODE"),
            pl.col("GENDER").alias("SEX"),
            pl.col("RACE").alias("RACE"),
            pl.col("AGE").alias("AGE_VALUE"),
            pl.col("INMATEID").alias("PUBLIC_PERSON_ID"),
            pl.lit("INMATEID").alias("PUBLIC_PERSON_ID_TYPE"),
        )
    )

    spine = pl.concat([arrests, complaints, summonses, admissions, discharges], how="diagonal_relaxed")
    spine.sink_parquet(out_parquet)
    pl.scan_parquet(out_parquet).sink_csv(out_csv)

    source_counts_df = (
        pl.scan_parquet(out_parquet).group_by("EVENT_SOURCE").agg(pl.len().alias("n")).collect()
    )
    summary = {
        "year": year,
        "output_parquet": str(out_parquet),
        "output_csv": str(out_csv),
        "rows_written": int(pl.scan_parquet(out_parquet).select(pl.len()).collect().item()),
        "source_counts": dict(zip(source_counts_df["EVENT_SOURCE"].to_list(), source_counts_df["n"].to_list())),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
