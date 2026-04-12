#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


DERIVED = Path("data/derived")
RAW = Path("data/raw")
META = Path("data/meta")


def parse_date(value: str, fmt: str) -> datetime:
    return datetime.strptime(value, fmt)


def clean(value: str | None) -> str:
    return (value or "").strip()


FIELDNAMES = [
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


def write_row(writer: csv.DictWriter, row: dict[str, str]) -> None:
    writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()

    arrests_path = DERIVED / f"nypd_arrests_{args.year}_research_dataset.csv"
    complaints_path = RAW / f"nypd_complaints_{args.year}_minimal.csv"
    summonses_path = RAW / "nypd_summonses_historic.csv"
    admissions_path = RAW / "doc_inmate_admissions.csv"
    discharges_path = RAW / "doc_inmate_discharges.csv"

    out_path = DERIVED / f"public_event_spine_{args.year}.csv"
    summary_path = META / f"public_event_spine_{args.year}_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    counts = Counter()

    with out_path.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDNAMES)
        writer.writeheader()

        with arrests_path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                related = clean(row.get("UNIQUE_DEMO_CMPLNT_NUM")) or clean(row.get("UNIQUE_BASE_CMPLNT_NUM"))
                write_row(
                    writer,
                    {
                        "EVENT_SOURCE": "nypd_arrests",
                        "EVENT_STAGE": "arrest",
                        "EVENT_KEY": clean(row.get("ARREST_KEY")),
                        "EVENT_DATE": datetime.strptime(row["ARREST_DATE"], "%m/%d/%Y").date().isoformat(),
                        "EVENT_YEAR": str(args.year),
                        "BORO": clean(row.get("ARREST_BORO_NM")),
                        "PRECINCT": clean(row.get("ARREST_PRECINCT")),
                        "OFFENSE_CODE": clean(row.get("KY_CD")),
                        "OFFENSE_DESC": clean(row.get("OFNS_DESC")),
                        "LAW_CATEGORY": clean(row.get("LAW_CAT_CD")),
                        "SEX": clean(row.get("PERP_SEX")),
                        "RACE": clean(row.get("PERP_RACE")),
                        "AGE_BUCKET": clean(row.get("AGE_GROUP")),
                        "LATITUDE": clean(row.get("LATITUDE")),
                        "LONGITUDE": clean(row.get("LONGITUDE")),
                        "RELATED_EVENT_KEY": related,
                        "RELATED_EVENT_TYPE": "complaint" if related else "",
                        "LINK_STATUS": clean(row.get("COMPLAINT_MATCH_STATUS")),
                    },
                )
                counts["nypd_arrests"] += 1

        with complaints_path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                write_row(
                    writer,
                    {
                        "EVENT_SOURCE": "nypd_complaints",
                        "EVENT_STAGE": "complaint",
                        "EVENT_KEY": clean(row.get("cmplnt_num")),
                        "EVENT_DATE": row["cmplnt_fr_dt"][:10],
                        "EVENT_YEAR": str(args.year),
                        "BORO": clean(row.get("boro_nm")),
                        "PRECINCT": clean(row.get("addr_pct_cd")),
                        "OFFENSE_CODE": clean(row.get("ky_cd")),
                        "OFFENSE_DESC": clean(row.get("ofns_desc")),
                        "LAW_CATEGORY": clean(row.get("law_cat_cd")),
                        "SEX": clean(row.get("susp_sex")),
                        "RACE": clean(row.get("susp_race")),
                        "AGE_BUCKET": clean(row.get("susp_age_group")),
                        "LATITUDE": clean(row.get("latitude")),
                        "LONGITUDE": clean(row.get("longitude")),
                    },
                )
                counts["nypd_complaints"] += 1

        with summonses_path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                event_dt = parse_date(row["SUMMONS_DATE"], "%m/%d/%Y")
                if event_dt.year != args.year:
                    continue
                write_row(
                    writer,
                    {
                        "EVENT_SOURCE": "nypd_summonses",
                        "EVENT_STAGE": "summons",
                        "EVENT_KEY": clean(row.get("SUMMONS_KEY")),
                        "EVENT_DATE": event_dt.date().isoformat(),
                        "EVENT_YEAR": str(args.year),
                        "BORO": clean(row.get("BORO")),
                        "PRECINCT": clean(row.get("PRECINCT_OF_OCCUR")),
                        "OFFENSE_CODE": clean(row.get("LAW_SECTION_NUMBER")),
                        "OFFENSE_DESC": clean(row.get("OFFENSE_DESCRIPTION")),
                        "LAW_CATEGORY": clean(row.get("SUMMONS_CATEGORY_TYPE")),
                        "SEX": clean(row.get("SEX")),
                        "RACE": clean(row.get("RACE")),
                        "AGE_BUCKET": clean(row.get("AGE_GROUP")),
                        "LATITUDE": clean(row.get("Latitude")),
                        "LONGITUDE": clean(row.get("Longitude")),
                    },
                )
                counts["nypd_summonses"] += 1

        with admissions_path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                event_dt = parse_date(row["ADMITTED_DT"], "%m/%d/%Y %I:%M:%S %p")
                if event_dt.year != args.year:
                    continue
                write_row(
                    writer,
                    {
                        "EVENT_SOURCE": "doc_admissions",
                        "EVENT_STAGE": "custody_admission",
                        "EVENT_KEY": f"{clean(row.get('INMATEID'))}|{clean(row.get('ADMITTED_DT'))}",
                        "EVENT_DATE": event_dt.date().isoformat(),
                        "EVENT_YEAR": str(args.year),
                        "OFFENSE_CODE": clean(row.get("TOP_CHARGE")),
                        "SEX": clean(row.get("GENDER")),
                        "RACE": clean(row.get("RACE")),
                        "PUBLIC_PERSON_ID": clean(row.get("INMATEID")),
                        "PUBLIC_PERSON_ID_TYPE": "INMATEID",
                    },
                )
                counts["doc_admissions"] += 1

        with discharges_path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                event_dt = parse_date(row["DISCHARGED_DT"], "%m/%d/%Y %I:%M:%S %p")
                if event_dt.year != args.year:
                    continue
                write_row(
                    writer,
                    {
                        "EVENT_SOURCE": "doc_discharges",
                        "EVENT_STAGE": "custody_discharge",
                        "EVENT_KEY": f"{clean(row.get('INMATEID'))}|{clean(row.get('DISCHARGED_DT'))}",
                        "EVENT_DATE": event_dt.date().isoformat(),
                        "EVENT_YEAR": str(args.year),
                        "OFFENSE_CODE": clean(row.get("TOP_CHARGE")),
                        "SEX": clean(row.get("GENDER")),
                        "RACE": clean(row.get("RACE")),
                        "AGE_VALUE": clean(row.get("AGE")),
                        "PUBLIC_PERSON_ID": clean(row.get("INMATEID")),
                        "PUBLIC_PERSON_ID_TYPE": "INMATEID",
                    },
                )
                counts["doc_discharges"] += 1

    summary = {
        "year": args.year,
        "output_path": str(out_path),
        "source_counts": dict(counts),
        "rows_written": sum(counts.values()),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
