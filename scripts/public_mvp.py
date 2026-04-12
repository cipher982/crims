#!/usr/bin/env python3

# %%
# Small notebook-style exploration for public NYC criminal-justice data.
# Run cell by cell in an editor that understands `# %%`, or run the whole file.

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pprint import pprint
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://data.cityofnewyork.us/resource/{dataset}.json"


def fetch_rows(dataset: str, *, select: list[str], order_by: str, limit: int = 5):
    params = {
        "$select": ",".join(select),
        "$order": f"{order_by} DESC",
        "$limit": str(limit),
    }
    url = BASE_URL.format(dataset=dataset) + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "crims-explore/0.1"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def head(rows, n: int = 5):
    pprint(rows[:n], sort_dicts=False)


def count_by(rows, field: str, n: int = 10):
    counts = Counter(row.get(field, "(missing)") for row in rows)
    pprint(counts.most_common(n))


def iso_day(value: str | None):
    if not value or value == "(null)":
        return None
    return value[:10]


def days_between(start: str | None, end: str | None):
    if not start or not end:
        return None
    start_dt = datetime.fromisoformat(start.replace("Z", ""))
    end_dt = datetime.fromisoformat(end.replace("Z", ""))
    return round((end_dt - start_dt).total_seconds() / 86400, 2)


# %%
# Step 1: recent arrests

arrests = fetch_rows(
    "8h9b-rp9u",
    select=[
        "arrest_key",
        "arrest_date",
        "pd_cd",
        "pd_desc",
        "ky_cd",
        "ofns_desc",
        "law_cat_cd",
        "arrest_boro",
        "arrest_precinct",
        "age_group",
        "perp_sex",
        "perp_race",
    ],
    order_by="arrest_date",
    limit=20,
)

print("Recent arrests:")
head(arrests, 5)


# %%
# Step 2: simple arrest distribution checks

print("Arrest categories:")
count_by(arrests, "law_cat_cd")

print("Arrest precincts:")
count_by(arrests, "arrest_precinct")


# %%
# Step 3: recent complaints

complaints = fetch_rows(
    "qgea-i56i",
    select=[
        "cmplnt_num",
        "cmplnt_fr_dt",
        "addr_pct_cd",
        "boro_nm",
        "pd_cd",
        "pd_desc",
        "ky_cd",
        "ofns_desc",
        "law_cat_cd",
        "susp_age_group",
        "susp_sex",
        "susp_race",
    ],
    order_by="cmplnt_fr_dt",
    limit=20,
)

print("Recent complaints:")
head(complaints, 5)


# %%
# Step 4: simple complaint distribution checks

print("Complaint categories:")
count_by(complaints, "law_cat_cd")

print("Complaint precincts:")
count_by(complaints, "addr_pct_cd")


# %%
# Step 5: recent DOC admissions and discharges

admissions = fetch_rows(
    "6teu-xtgp",
    select=[
        "inmateid",
        "admitted_dt",
        "discharged_dt",
        "top_charge",
        "gender",
        "race",
        "inmate_status_code",
    ],
    order_by="admitted_dt",
    limit=20,
)

discharges = fetch_rows(
    "94ri-3ium",
    select=[
        "inmateid",
        "admitted_dt",
        "discharged_dt",
        "top_charge",
        "gender",
        "race",
        "inmate_status_code",
    ],
    order_by="discharged_dt",
    limit=20,
)

print("Recent admissions:")
head(admissions, 5)

print("Recent discharges:")
head(discharges, 5)


# %%
# Step 6: first exact join we can trust: admissions -> discharges on inmateid

discharges_by_inmate = {row["inmateid"]: row for row in discharges if row.get("inmateid")}

doc_matches = []
for admission in admissions:
    inmateid = admission.get("inmateid")
    if inmateid and inmateid in discharges_by_inmate:
        discharge = discharges_by_inmate[inmateid]
        doc_matches.append(
            {
                "inmateid": inmateid,
                "admitted_day": iso_day(admission.get("admitted_dt")),
                "discharged_day": iso_day(discharge.get("discharged_dt")),
                "top_charge_at_admission": admission.get("top_charge"),
                "top_charge_at_discharge": discharge.get("top_charge"),
                "days_in_sample": days_between(
                    admission.get("admitted_dt"), discharge.get("discharged_dt")
                ),
            }
        )

print(f"Exact DOC matches in the 20x20 sample: {len(doc_matches)}")
head(doc_matches, 5)


# %%
# Step 7: tiny exploratory arrest <-> complaint candidate join.
# This is deliberately conservative and only meant to show ambiguity.

candidate_pairs = []
for complaint in complaints:
    for arrest in arrests:
        if iso_day(complaint.get("cmplnt_fr_dt")) != iso_day(arrest.get("arrest_date")):
            continue
        if complaint.get("addr_pct_cd") != arrest.get("arrest_precinct"):
            continue
        if complaint.get("ky_cd") != arrest.get("ky_cd"):
            continue
        candidate_pairs.append(
            {
                "cmplnt_num": complaint.get("cmplnt_num"),
                "arrest_key": arrest.get("arrest_key"),
                "date": iso_day(complaint.get("cmplnt_fr_dt")),
                "precinct": complaint.get("addr_pct_cd"),
                "ky_cd": complaint.get("ky_cd"),
            }
        )

print(f"Same-day same-precinct same-ky_cd complaint/arrest candidates: {len(candidate_pairs)}")
head(candidate_pairs, 10)
