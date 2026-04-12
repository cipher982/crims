#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


BORO_MAP = {
    "M": "MANHATTAN",
    "B": "BRONX",
    "K": "BROOKLYN",
    "Q": "QUEENS",
    "S": "STATEN ISLAND",
}


def clean(value: str | None) -> str:
    value = (value or "").strip().upper()
    return "" if value in {"", "(NULL)", "UNKNOWN", "U"} else value


def arrest_key_tuple(row: dict[str, str]) -> tuple[str, str, str, str]:
    day = datetime.strptime(row["ARREST_DATE"], "%m/%d/%Y").date().isoformat()
    return (
        day,
        clean(row.get("ARREST_PRECINCT")),
        clean(row.get("KY_CD")),
        BORO_MAP.get(clean(row.get("ARREST_BORO")), ""),
    )


def complaint_key_tuple(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row["cmplnt_fr_dt"][:10],
        clean(row.get("addr_pct_cd")),
        clean(row.get("ky_cd")),
        clean(row.get("boro_nm")),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()

    arrests_path = Path("data/raw/nypd_arrests_historic.csv")
    complaints_path = Path(f"data/raw/nypd_complaints_{args.year}_minimal.csv")
    out_path = Path(f"data/derived/nypd_arrests_{args.year}_research_dataset.csv")
    summary_path = Path(f"data/meta/nypd_arrests_{args.year}_research_dataset_summary.json")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    complaint_index = defaultdict(list)
    with complaints_path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            complaint_index[complaint_key_tuple(row)].append(row)

    fieldnames = [
        "ARREST_KEY",
        "ARREST_DATE",
        "ARREST_BORO",
        "ARREST_BORO_NM",
        "ARREST_PRECINCT",
        "X_COORD_CD",
        "Y_COORD_CD",
        "LATITUDE",
        "LONGITUDE",
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
        "UNIQUE_BASE_CMPLNT_NUM",
        "UNIQUE_BASE_COMPLAINT_OFNS_DESC",
        "UNIQUE_DEMO_CMPLNT_NUM",
        "UNIQUE_DEMO_COMPLAINT_OFNS_DESC",
        "UNIQUE_DEMO_COMPLAINT_LAW_CAT_CD",
    ]

    status_counts = Counter()
    output_rows = 0

    with arrests_path.open(newline="") as source, out_path.open("w", newline="") as out:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            arrest_day = datetime.strptime(row["ARREST_DATE"], "%m/%d/%Y").date()
            if arrest_day.year != args.year:
                continue

            base_candidates = complaint_index.get(arrest_key_tuple(row), [])
            demo_candidates = base_candidates

            sex = clean(row.get("PERP_SEX"))
            race = clean(row.get("PERP_RACE"))
            age = clean(row.get("AGE_GROUP"))

            if sex:
                demo_candidates = [r for r in demo_candidates if clean(r.get("susp_sex")) in {"", sex}]
            if race:
                demo_candidates = [r for r in demo_candidates if clean(r.get("susp_race")) in {"", race}]
            if age:
                demo_candidates = [r for r in demo_candidates if clean(r.get("susp_age_group")) in {"", age}]

            base_count = len(base_candidates)
            demo_count = len(demo_candidates)

            if demo_count == 1:
                match_status = "unique_demo"
            elif demo_count > 1:
                match_status = "ambiguous_demo"
            elif base_count == 1:
                match_status = "unique_base"
            elif base_count > 1:
                match_status = "ambiguous_base"
            else:
                match_status = "none"

            status_counts[match_status] += 1
            unique_base = base_candidates[0] if base_count == 1 else None
            unique_demo = demo_candidates[0] if demo_count == 1 else None

            writer.writerow(
                {
                    "ARREST_KEY": row["ARREST_KEY"],
                    "ARREST_DATE": row["ARREST_DATE"],
                    "ARREST_BORO": row["ARREST_BORO"],
                    "ARREST_BORO_NM": BORO_MAP.get(clean(row.get("ARREST_BORO")), ""),
                    "ARREST_PRECINCT": row["ARREST_PRECINCT"],
                    "X_COORD_CD": row["X_COORD_CD"],
                    "Y_COORD_CD": row["Y_COORD_CD"],
                    "LATITUDE": row["Latitude"],
                    "LONGITUDE": row["Longitude"],
                    "PD_CD": row["PD_CD"],
                    "PD_DESC": row["PD_DESC"],
                    "KY_CD": row["KY_CD"],
                    "OFNS_DESC": row["OFNS_DESC"],
                    "LAW_CAT_CD": row["LAW_CAT_CD"],
                    "AGE_GROUP": row["AGE_GROUP"],
                    "PERP_SEX": row["PERP_SEX"],
                    "PERP_RACE": row["PERP_RACE"],
                    "COMPLAINT_BASE_COUNT": base_count,
                    "COMPLAINT_DEMO_COUNT": demo_count,
                    "COMPLAINT_MATCH_STATUS": match_status,
                    "UNIQUE_BASE_CMPLNT_NUM": unique_base["cmplnt_num"] if unique_base else "",
                    "UNIQUE_BASE_COMPLAINT_OFNS_DESC": unique_base["ofns_desc"] if unique_base else "",
                    "UNIQUE_DEMO_CMPLNT_NUM": unique_demo["cmplnt_num"] if unique_demo else "",
                    "UNIQUE_DEMO_COMPLAINT_OFNS_DESC": unique_demo["ofns_desc"] if unique_demo else "",
                    "UNIQUE_DEMO_COMPLAINT_LAW_CAT_CD": unique_demo["law_cat_cd"] if unique_demo else "",
                }
            )
            output_rows += 1

    summary = {
        "year": args.year,
        "output_path": str(out_path),
        "rows_written": output_rows,
        "status_counts": dict(status_counts),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
