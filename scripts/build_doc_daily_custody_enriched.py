#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


RAW_DAILY = Path("data/raw/doc_daily_inmates_in_custody.csv")
EPISODES = Path("data/derived/doc_custody_episodes_joined.csv")
OUT = Path("data/derived/doc_daily_custody_enriched.csv")
SUMMARY = Path("data/meta/doc_daily_custody_enriched_summary.json")


def key(row: dict[str, str]) -> tuple[str, str]:
    return ((row.get("INMATEID") or "").strip(), (row.get("ADMITTED_DT") or "").strip())


def norm(value: str | None) -> str:
    return (value or "").strip()


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)

    episodes = {}
    for row in csv.DictReader(EPISODES.open(newline="")):
        episodes[key(row)] = row

    fieldnames = [
        "INMATEID",
        "ADMITTED_DT",
        "DAILY_DISCHARGED_DT",
        "CUSTODY_LEVEL",
        "BRADH",
        "RACE",
        "GENDER",
        "AGE",
        "INMATE_STATUS_CODE",
        "SEALED",
        "SRG_FLG",
        "TOP_CHARGE",
        "INFRACTION",
        "DISCHARGE_LINK_MATCH_TYPE",
        "EPISODE_DISCHARGE_DISCHARGED_DT",
        "EPISODE_DISCHARGE_STATUS",
        "EPISODE_ADMISSION_TOP_CHARGE",
        "EPISODE_DISCHARGE_TOP_CHARGE",
    ]

    status_counts = Counter()
    match_counts = Counter()
    rows_written = 0

    with RAW_DAILY.open(newline="") as source, OUT.open("w", newline="") as out:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            episode = episodes.get(key(row))
            match_type = episode["MATCH_TYPE"] if episode else "missing_admission_episode"
            match_counts[match_type] += 1
            status_counts[norm(row.get("INMATE_STATUS_CODE"))] += 1

            writer.writerow(
                {
                    "INMATEID": norm(row.get("INMATEID")),
                    "ADMITTED_DT": norm(row.get("ADMITTED_DT")),
                    "DAILY_DISCHARGED_DT": norm(row.get("DISCHARGED_DT")),
                    "CUSTODY_LEVEL": norm(row.get("CUSTODY_LEVEL")),
                    "BRADH": norm(row.get("BRADH")),
                    "RACE": norm(row.get("RACE")),
                    "GENDER": norm(row.get("GENDER")),
                    "AGE": norm(row.get("AGE")),
                    "INMATE_STATUS_CODE": norm(row.get("INMATE_STATUS_CODE")),
                    "SEALED": norm(row.get("SEALED")),
                    "SRG_FLG": norm(row.get("SRG_FLG")),
                    "TOP_CHARGE": norm(row.get("TOP_CHARGE")),
                    "INFRACTION": norm(row.get("INFRACTION")),
                    "DISCHARGE_LINK_MATCH_TYPE": match_type,
                    "EPISODE_DISCHARGE_DISCHARGED_DT": norm(episode.get("DISCHARGE_DISCHARGED_DT")) if episode else "",
                    "EPISODE_DISCHARGE_STATUS": norm(episode.get("DISCHARGE_STATUS")) if episode else "",
                    "EPISODE_ADMISSION_TOP_CHARGE": norm(episode.get("ADMISSION_TOP_CHARGE")) if episode else "",
                    "EPISODE_DISCHARGE_TOP_CHARGE": norm(episode.get("DISCHARGE_TOP_CHARGE")) if episode else "",
                }
            )
            rows_written += 1

    summary = {
        "rows_written": rows_written,
        "discharge_link_match_counts": dict(match_counts),
        "daily_status_counts": dict(status_counts),
        "output_path": str(OUT),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
