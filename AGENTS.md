# AGENTS.md

## Project Overview

**crims** is a lean research workspace for assembling the best possible public NYC criminal-justice dataset, understanding what can be joined, and identifying where public access stops.

## Tech Stack

| Category | Technology |
| --- | --- |
| Language(s) | Python 3 |
| Framework(s) | none |
| Database(s) | local files first; Parquet as canonical processed layer; optional DuckDB for ad hoc analysis |
| Key dependencies | Polars for scans/joins/writes; stdlib for small glue code; add more only when they unlock clear value |

## Build & Test

| Action | Command |
| --- | --- |
| Run exploration file | `uv run python scripts/public_mvp.py` |
| Build canonical event spine | `uv run python scripts/build_public_event_spine_polars.py --year 2024` |
| Enrich spine with Census geographies | `uv run python scripts/build_public_event_spine_census_geo.py --year 2024` |
| Build multi-year panel | `uv run python scripts/build_public_event_panel.py --start-year 2014 --end-year 2024` |
| Profile panel | `uv run python scripts/profile_public_event_panel.py --path data/derived/public_event_panel_2014_2024_census_geo.parquet` |
| Run a one-off Python check | `uv run python -c "..."` |
| List raw data | `find data -maxdepth 2 -type f | sort` |

## Architecture Overview

This repo should stay simple. The core flow is:

1. acquire raw public datasets locally
2. inspect heads, keys, nulls, and date coverage
3. turn raw CSV into tidy Parquet-backed yearly datasets with Polars lazy scans
4. test one join at a time
5. keep exact joins separate from heuristic joins
6. geocode only unique coordinate pairs, cache the results locally, and join them back in
7. document what is trustworthy and what is not

Prefer notebook-style exploration over early pipeline design.

## Working Vision

- Build the best public raw dataset we can without pretending public records support a full named person graph.
- Treat this as an `event graph` first: arrests, complaints, summonses, jail admissions, jail discharges, daily custody snapshots.
- Use restricted-data planning only after the public path is exhausted.

## Success Criteria

Current strong outcome:

- keep one singular tidy yearly event-spine dataset as the main research table
- prefer the census-enriched panel Parquet as the active canonical output when it exists
- make Parquet the canonical processed format and keep CSV exports opt-in
- keep exact joins, candidate joins, and unsupported joins clearly labeled
- enrich event rows with stable public geography such as tract and block group where coordinates exist
- keep one compact machine-readable profile for the active panel so quality and coverage can be checked quickly
- treat older years as lower-confidence for heuristic arrest-to-complaint linkage until profiling says otherwise
- preserve raw source files locally and keep them out of git
- keep repo docs and scripts concise enough to stay inspectable

## Conventions

- Keep notes in as few files as possible.
- Prefer visible, incremental exploration to large opaque scripts.
- When trying joins, start tiny and inspect actual matched rows.
- Separate `exact`, `candidate`, and `unsupported` joins explicitly.
- Flag stale or suspicious feeds immediately.
- Prefer Polars expressions and lazy scans over Python row loops for repeatable transforms.
- Geocode deduplicated coordinates once, cache them, and reuse the cache on reruns.

## Plan Mode

- Keep plans short.
- Prefer the next concrete data step over abstract architecture.

## Agent Responsibilities

1. Pull real data, not just metadata.
2. Validate assumptions against live endpoints.
3. Preserve raw copies before transforming.
4. Keep scope focused on public-data assembly and joinability.

## Boundaries

- **Always do**: inspect schema and sample rows before broad transforms; keep raw data intact; note known quality issues
- **Ask first**: broad dependency additions, major repo restructuring, nonpublic data requests sent externally
- **Never do**: fabricate joins, imply fuzzy matches are ground truth, overwrite raw downloads, create doc sprawl

## Git Workflows

- This workspace is a git repo.
- Keep commits small and source-only.
- Raw and derived data stay out of version control unless explicitly requested.

## Updating This File

Update this file when the workflow changes, when a join rule proves brittle, or when a better success criterion becomes obvious from the data.
