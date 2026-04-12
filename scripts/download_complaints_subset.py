#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


FIELDS = [
    "cmplnt_num",
    "cmplnt_fr_dt",
    "addr_pct_cd",
    "boro_nm",
    "pd_cd",
    "ky_cd",
    "ofns_desc",
    "law_cat_cd",
    "susp_age_group",
    "susp_sex",
    "susp_race",
    "latitude",
    "longitude",
]


def fetch_rows(where: str, offset: int, limit: int) -> list[dict[str, str]]:
    params = {
        "$select": ",".join(FIELDS),
        "$where": where,
        "$limit": str(limit),
        "$offset": str(offset),
        "$order": "cmplnt_fr_dt,cmplnt_num",
    }
    url = "https://data.cityofnewyork.us/resource/qgea-i56i.json?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "crims-complaints-subset/0.1"})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def download_year(year: int, limit: int) -> dict[str, object]:
    out = Path(f"data/raw/nypd_complaints_{year}_minimal.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    where = (
        f'cmplnt_fr_dt between "{year}-01-01T00:00:00.000" '
        f'and "{year}-12-31T23:59:59.999"'
    )

    offset = 0
    total = 0
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()

        while True:
            rows = fetch_rows(where, offset=offset, limit=limit)
            if not rows:
                break
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in FIELDS})
            total += len(rows)
            offset += len(rows)
            print(f"year={year} rows_written {total}", flush=True)

    return {"year": year, "output": str(out), "rows_written": total}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int)
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--limit", type=int, default=50000)
    args = parser.parse_args()

    if args.year is None and (args.start_year is None or args.end_year is None):
        parser.error("provide --year or both --start-year and --end-year")
    if args.year is not None and (args.start_year is not None or args.end_year is not None):
        parser.error("use either --year or --start-year/--end-year, not both")

    if args.year is not None:
        years = [args.year]
    else:
        if args.start_year > args.end_year:
            parser.error("--start-year must be <= --end-year")
        years = list(range(args.start_year, args.end_year + 1))

    results = [download_year(year, limit=args.limit) for year in years]
    print(json.dumps({"years": results}, indent=2))


if __name__ == "__main__":
    main()
