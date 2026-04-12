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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--limit", type=int, default=50000)
    args = parser.parse_args()

    out = Path(f"data/raw/nypd_complaints_{args.year}_minimal.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    where = (
        f'cmplnt_fr_dt between "{args.year}-01-01T00:00:00.000" '
        f'and "{args.year}-12-31T23:59:59.999"'
    )

    offset = 0
    total = 0
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()

        while True:
            rows = fetch_rows(where, offset=offset, limit=args.limit)
            if not rows:
                break
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in FIELDS})
            total += len(rows)
            offset += len(rows)
            print(f"rows_written {total}", flush=True)

    print(json.dumps({"output": str(out), "rows_written": total}, indent=2))


if __name__ == "__main__":
    main()
