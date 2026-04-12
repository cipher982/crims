#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


RAW_DIR = Path("data/raw")
DERIVED_DIR = Path("data/derived")
META_DIR = Path("data/meta")

ADMISSIONS = RAW_DIR / "doc_inmate_admissions.csv"
DISCHARGES = RAW_DIR / "doc_inmate_discharges.csv"
OUTPUT = DERIVED_DIR / "doc_custody_episodes_joined.csv"
SUMMARY = META_DIR / "doc_custody_episodes_summary.json"


def norm(value: str | None) -> str:
    return (value or "").strip()


def episode_key(row: dict[str, str]) -> tuple[str, str]:
    return (norm(row.get("INMATEID")), norm(row.get("ADMITTED_DT")))


def full_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (norm(row.get("INMATEID")), norm(row.get("ADMITTED_DT")), norm(row.get("DISCHARGED_DT")))


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    discharge_by_full = {}
    discharge_by_episode = {}
    discharge_full_duplicates = 0
    discharge_episode_duplicates = 0
    for row in csv.DictReader(DISCHARGES.open(newline="")):
        fkey = full_key(row)
        ekey = episode_key(row)
        if fkey in discharge_by_full:
            discharge_full_duplicates += 1
        discharge_by_full[fkey] = row
        discharge_by_episode.setdefault(ekey, []).append(row)
        if len(discharge_by_episode[ekey]) > 1:
            discharge_episode_duplicates += 1

    fieldnames = [
        "INMATEID",
        "ADMITTED_DT",
        "ADMISSION_DISCHARGED_DT",
        "DISCHARGE_DISCHARGED_DT",
        "MATCH_TYPE",
        "ADMISSION_RACE",
        "DISCHARGE_RACE",
        "ADMISSION_GENDER",
        "DISCHARGE_GENDER",
        "DISCHARGE_AGE",
        "ADMISSION_STATUS",
        "DISCHARGE_STATUS",
        "ADMISSION_TOP_CHARGE",
        "DISCHARGE_TOP_CHARGE",
    ]

    exact_matched = 0
    candidate_matched = 0
    unmatched = 0
    same_top_charge_exact = 0
    same_top_charge_candidate = 0
    status_pairs = Counter()

    with ADMISSIONS.open(newline="") as source, OUTPUT.open("w", newline="") as out:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            exact = discharge_by_full.get(full_key(row))
            candidates = discharge_by_episode.get(episode_key(row), [])
            discharge = None
            match_type = "unmatched"

            if exact:
                discharge = exact
                match_type = "exact_full_key"
                exact_matched += 1
                if norm(row.get("TOP_CHARGE")) and norm(row.get("TOP_CHARGE")) == norm(discharge.get("TOP_CHARGE")):
                    same_top_charge_exact += 1
                status_pairs[(norm(row.get("INMATE_STATUS_CODE")), norm(discharge.get("INMATE_STATUS_CODE")))] += 1
            elif len(candidates) == 1:
                discharge = candidates[0]
                match_type = "candidate_inmateid_admitted_dt"
                candidate_matched += 1
                if norm(row.get("TOP_CHARGE")) and norm(row.get("TOP_CHARGE")) == norm(discharge.get("TOP_CHARGE")):
                    same_top_charge_candidate += 1
            else:
                unmatched += 1

            writer.writerow(
                {
                    "INMATEID": norm(row.get("INMATEID")),
                    "ADMITTED_DT": norm(row.get("ADMITTED_DT")),
                    "ADMISSION_DISCHARGED_DT": norm(row.get("DISCHARGED_DT")),
                    "DISCHARGE_DISCHARGED_DT": norm(discharge.get("DISCHARGED_DT")) if discharge else "",
                    "MATCH_TYPE": match_type,
                    "ADMISSION_RACE": norm(row.get("RACE")),
                    "DISCHARGE_RACE": norm(discharge.get("RACE")) if discharge else "",
                    "ADMISSION_GENDER": norm(row.get("GENDER")),
                    "DISCHARGE_GENDER": norm(discharge.get("GENDER")) if discharge else "",
                    "DISCHARGE_AGE": norm(discharge.get("AGE")) if discharge else "",
                    "ADMISSION_STATUS": norm(row.get("INMATE_STATUS_CODE")),
                    "DISCHARGE_STATUS": norm(discharge.get("INMATE_STATUS_CODE")) if discharge else "",
                    "ADMISSION_TOP_CHARGE": norm(row.get("TOP_CHARGE")),
                    "DISCHARGE_TOP_CHARGE": norm(discharge.get("TOP_CHARGE")) if discharge else "",
                }
            )

    summary = {
        "admission_rows": exact_matched + candidate_matched + unmatched,
        "exact_full_key_matches": exact_matched,
        "candidate_inmateid_admitted_dt_matches": candidate_matched,
        "unmatched_admission_rows": unmatched,
        "share_exact_matched": round(exact_matched / (exact_matched + candidate_matched + unmatched), 4)
        if (exact_matched + candidate_matched + unmatched)
        else 0,
        "share_candidate_matched": round(candidate_matched / (exact_matched + candidate_matched + unmatched), 4)
        if (exact_matched + candidate_matched + unmatched)
        else 0,
        "same_top_charge_when_exact_match": same_top_charge_exact,
        "same_top_charge_when_candidate_match": same_top_charge_candidate,
        "discharge_full_key_duplicates": discharge_full_duplicates,
        "discharge_episode_key_duplicates": discharge_episode_duplicates,
        "top_status_pairs": [[a, b, n] for (a, b), n in status_pairs.most_common(10)],
        "output_path": str(OUTPUT),
    }

    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
