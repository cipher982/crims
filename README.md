# crims

Focused workspace for figuring out what NYC criminal-justice data we can compile publicly, what joins are actually possible, and where the public path stops.

## Identifier Ceiling

The public bulk path currently gives us:

- event IDs like `ARREST_KEY`, `CMPLNT_NUM`, `SUMMONS_KEY`
- custody IDs like `INMATEID`
- offense, time, geography, and suspect demographic buckets

The public bulk path does **not** currently give us:

- names
- full date of birth
- street address
- a shared person identifier across arrest, court, jail, and conviction

So the working goal is a clean, well-labeled public research dataset with the best available exposed identifiers and explicit match confidence, while continuing to look for lawful ways to add stronger identifiers later.

## Current Bearings

- The strongest public backbone is event-level NYC Open Data, especially NYPD arrests, complaints, summonses, and DOC custody datasets.
- Public bulk data is good for an `event graph`, not a named `person graph`.
- Exact public joins exist inside a stage when a local key is exposed:
  - arrests: `arrest_key`
  - complaints: `cmplnt_num`
  - summonses: `summons_key`
  - DOC custody: `inmateid`
- Public cross-stage joins are weak because there is no shared exposed key from arrest to court to jail to conviction.
- If we ever get restricted data, the real backbone is likely some combination of `NYSID`, `CJTN`, court case number, and local custody IDs. Publicly, we do not have that.

## Working Model

Start from what we can do now:

1. Build a clean inventory of public sources and their keys.
2. Pull samples and recent windows from those sources.
3. Prove which joins are exact.
4. Try a few conservative heuristic joins across sources and measure ambiguity.
5. Only after that decide whether a restricted-data track is necessary.

## MVPs

### MVP 1: Public Source Census

Goal: list the public datasets that are actually scriptable and useful.

Output:

- one tight source manifest
- one prototype fetch script

### MVP 2: Exact Public Joins

Goal: validate joins where the public data already gives a true key.

Initial target:

- DOC admissions -> discharges via `inmateid`

### MVP 3: Heuristic Public Joins

Goal: see whether arrest, complaint, and summons data can be linked at all without person identifiers.

Initial target:

- complaint -> arrest candidate matches using offense code, precinct, borough, date window, and suspect demographics when present

The point is not to pretend this is ground truth. The point is to quantify how noisy the public-only path is.

## Run

```bash
uv run python scripts/public_mvp.py
uv run python scripts/download_public_data.py <optional-slugs>
uv run python scripts/download_complaints_subset.py --year 2024
uv run python scripts/download_complaints_subset.py --start-year 2023 --end-year 2024
uv run python scripts/build_doc_episode_dataset.py
uv run python scripts/build_doc_daily_custody_enriched.py
uv run python scripts/build_arrest_research_dataset.py --year 2024
uv run python scripts/build_public_event_spine.py --year 2024
uv run python scripts/build_arrest_research_dataset_polars.py --year 2024
uv run python scripts/build_public_event_spine_polars.py --year 2024
uv run python scripts/build_public_event_spine_census_geo.py --year 2024
uv run python scripts/build_public_event_panel.py --start-year 2018 --end-year 2024
uv run python scripts/profile_public_event_panel.py --path data/derived/public_event_panel_2018_2024_census_geo.parquet
```

`download_complaints_subset.py` now supports either a single `--year` or a `--start-year/--end-year` range.

Open the file in VS Code or another editor that supports `# %%` cells if you want a notebook-like flow.

## Scope Discipline

- Keep notes tight.
- Avoid extra docs unless they replace an existing one.
- Prefer one script over a full pipeline until the joins are defensible.

## Local Assets

Current local work has two layers:

- raw public files in `data/raw/`
- derived exact / candidate DOC episode joins in `data/derived/`

The machine-readable inventory lives in `data/meta/local_inventory.json`.
High-signal findings and join summaries live in `data/meta/session_findings.json`.

These generated data files are local artifacts and are intentionally ignored by git.

## Current Best Processed Datasets

- `data/derived/public_event_panel_2018_2024_census_geo.parquet`
  - current canonical seven-year public panel with Census geography attached where coordinates exist
- `data/derived/public_event_spine_2024_census_geo.parquet`
  - canonical single-year event spine with Census geography attached where public coordinates exist
- `data/derived/public_event_spine_2024.parquet`
  - pre-geography canonical columnar version of the unified 2024 event spine
- `data/derived/public_event_spine_2024.csv`
  - current singular tidy long-form public dataset across arrests, complaints, summonses, and DOC admissions / discharges for 2024
- `data/derived/nypd_arrests_2024_research_dataset.parquet`
  - canonical columnar version of the arrest-centered 2024 linkage dataset
- `data/derived/doc_custody_episodes_joined.csv`
  - exact and candidate custody episode joins from DOC admissions + discharges
- `data/derived/doc_daily_custody_enriched.csv`
  - current custody snapshot enriched with discharge-link status from the DOC episode build
- `data/derived/nypd_arrests_2024_research_dataset.csv`
  - arrest-centered 2024 file with public identifiers, location fields, and complaint-link candidate status

## Current Success Criteria

- keep `public_event_panel_2018_2024_census_geo.parquet` as the current canonical singular tidy dataset
- keep yearly `public_event_spine_<year>_census_geo.parquet` files as the reproducible building blocks
- keep `public_event_spine_2024.parquet` as the clean pre-geography staging layer
- keep `public_event_spine_2024.csv` as a convenience export when helpful
- enrich rows with stable geography like census tract / block group where public coordinates exist
- keep every linkage labeled as exact, candidate, or unsupported
- leave room for later institutional identifiers without pretending public data already provides them

Current profile output:

- `data/meta/public_event_panel_2018_2024_census_geo_profile.json`
  - per-year and per-source counts, geography coverage, key non-null coverage, and arrest link-status summaries

## Polars Rewrite

Rewrite targets:

- use Polars lazy scans from raw CSV instead of repeated row-by-row Python loops
- keep raw CSVs as immutable inputs
- make Parquet the canonical processed format
- keep CSV exports as convenience artifacts, not the primary internal format
- geocode only unique coordinate pairs, cache them locally, and join the cache back into the spine
- keep transforms expression-driven so query planning stays optimizable
- preserve the same exact / candidate / unsupported linkage semantics during the rewrite

Canonical flow:

1. raw CSV in `data/raw/`
2. Polars lazy scan + clean + join
3. canonical Parquet in `data/derived/`
4. optional CSV export
5. local JSON summary and local coordinate cache in `data/meta/`
