#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Dataset:
    slug: str
    dataset_id: str
    filename: str
    enabled: bool = True


DATASETS = [
    Dataset("arrests_historic", "8h9b-rp9u", "nypd_arrests_historic.csv"),
    Dataset("complaints_historic", "qgea-i56i", "nypd_complaints_historic.csv"),
    Dataset("summonses_historic", "sv2w-rv3k", "nypd_summonses_historic.csv"),
    Dataset("doc_admissions", "6teu-xtgp", "doc_inmate_admissions.csv"),
    Dataset("doc_discharges", "94ri-3ium", "doc_inmate_discharges.csv"),
    Dataset("doc_daily_custody", "7479-ugqb", "doc_daily_inmates_in_custody.csv"),
    Dataset("shooting_offenders", "gdk4-mbsv", "nypd_shooting_offenders.csv"),
]


RAW_DIR = Path("data/raw")
META_DIR = Path("data/meta")


def download_url(dataset_id: str) -> str:
    return f"https://data.cityofnewyork.us/api/views/{dataset_id}/rows.csv?accessType=DOWNLOAD"


def fetch(dataset: Dataset) -> dict:
    url = download_url(dataset.dataset_id)
    request = Request(url, headers={"User-Agent": "crims-download/0.1"})
    destination = RAW_DIR / dataset.filename
    tmp = destination.with_suffix(destination.suffix + ".part")

    with urlopen(request, timeout=120) as response, tmp.open("wb") as fh:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)

        headers = dict(response.headers.items())

    tmp.replace(destination)

    stat = destination.stat()
    return {
        "slug": dataset.slug,
        "dataset_id": dataset.dataset_id,
        "path": str(destination),
        "bytes": stat.st_size,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "last_modified": headers.get("Last-Modified"),
        "content_disposition": headers.get("Content-disposition"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "slugs",
        nargs="*",
        help="Optional dataset slugs to download. Default: all enabled datasets.",
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    selected = set(args.slugs)
    manifest = []
    for dataset in DATASETS:
        if not dataset.enabled:
            continue
        if selected and dataset.slug not in selected:
            continue
        print(f"downloading {dataset.slug} ...", flush=True)
        manifest.append(fetch(dataset))

    manifest_path = META_DIR / "downloads_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
