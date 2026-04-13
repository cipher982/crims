# crims

Research workspace for building the strongest possible public NYC criminal-justice dataset, with a practical focus on jail recidivism and arrest-to-jail linkage.

The core constraint is structural: public datasets expose event records, not named people. NYC DOC jail data includes a persistent `INMATEID`, so jail recidivism is measurable. NYPD, court, and most state datasets do not expose a cross-stage person key, so anything beyond jail-level recidivism is either heuristic or not currently feasible from public data alone.

## What Is Here

- `scripts/` contains the data download, cleaning, enrichment, and analysis pipeline.
- `web/` contains the primary Next.js explorer.
- `dashboard.py` is a legacy Streamlit fallback for quick local exploration.
- `SOURCES.md` inventories the public data sources, join surfaces, and access limits.

Raw and derived data are intentionally ignored. A fresh clone contains code and docs only.

## Quick Start

Python environment:

```bash
uv sync
```

Download public source data:

```bash
uv run python scripts/download_public_data.py
```

Build the core recidivism outputs:

```bash
uv run python scripts/analyze_doc_recidivism.py
uv run python scripts/analyze_doc_cohort_recidivism.py
uv run python scripts/build_arrest_doc_bridge.py
```

Run the primary web explorer:

```bash
cd web
bun install
bun run dev
```

Run the legacy Streamlit explorer:

```bash
uv run streamlit run dashboard.py
```

## Current Scope

- Exact jail recidivism is supported through NYC DOC `INMATEID`.
- Arrest-to-complaint linkage is partial and heuristic.
- Arrest-to-jail linkage exists for a narrow high-confidence subset.
- Court outcomes, statewide person-level recidivism, and prison linkage are not solved from public bulk data.

That boundary matters. The repo distinguishes exact joins, candidate joins, and unsupported joins explicitly instead of pretending fuzzy matches are ground truth.

## Data Layout

- `data/raw/` immutable CSV downloads
- `data/derived/` parquet outputs
- `data/meta/` inventories, profiles, and geocoding cache

The web app reads derived parquet files directly. For production deploys it only needs:

- `doc_recidivism_persons.parquet`
- `doc_recidivism_episodes.parquet`
- `doc_cohort_recidivism.parquet`
- `arrest_doc_bridge.parquet`

See [web/README.md](web/README.md) for the web app runtime and deployment details.

## Notes

- Source files stay in git. Data files do not.
- The canonical explorer is the Next.js app in `web/`.
- Methodology and source limitations are part of the project, not an afterthought. If a join is candidate-grade, it should be described that way in code and outputs.
