# crims

Research workspace for assembling the best possible public NYC criminal-justice dataset. The end goal is tracking recidivism and multi-arrest patterns over time. The current focus is exhausting the public data path before pursuing restricted-data agreements.

## The Problem

Public NYC bulk data gives us **event records**, not named people. There is no shared person identifier across criminal justice stages. The project treats this as an **event graph** and labels every linkage as exact, candidate, or unsupported.

### NYC Criminal Justice Pipeline — What Exists as Data

```
COMPLAINT ──> ARREST ──> ARRAIGNMENT ──> INDICTMENT/TRIAL ──> CONVICTION ──> JAIL ──> PRISON ──> PAROLE
    │            │              │                                               │        │
  NYPD         NYPD        OCA / UCS                                        NYC DOC   DOCCS
 (public)    (public)   (public, de-id)                                    (public)  (aggregate only)
```

| Stage | Dataset | Bulk? | Person ID? | In panel? |
|-------|---------|-------|------------|-----------|
| Complaint | NYPD Complaints `qgea-i56i` | Yes | No — `cmplnt_num` | Yes |
| Arrest | NYPD Arrests `8h9b-rp9u` | Yes | No — `arrest_key` | Yes |
| Summons | NYPD Summonses `sv2w-rv3k` | Yes | No — `summons_key` | Yes |
| Court (arraignment thru sentencing) | OCA-STAT Act extract | Yes (CSV) | No — de-identified | **Not yet** |
| Court (pretrial/bail detail) | OCA Pretrial Release extract | Yes (CSV) | `arr_cycle_id` links dockets within same arrest only | **Not yet** |
| Jail (NYC / Rikers) | DOC Admissions `6teu-xtgp` / Discharges `94ri-3ium` / Daily `7479-ugqb` | Yes | **`INMATEID`** (persistent) | Yes |
| Prison (state) | DOCCS Open Data NY | Aggregate only | No DIN/NYSID | No |
| Probation | NYC DOP | Aggregate only | No | No |
| Parole | DOCCS "Find a Parolee" | Interactive only | No | No |

### Identifier Ceiling

Public data exposes event IDs and demographic buckets (race, sex, age group). It does **not** expose names, DOB, addresses, or a cross-stage person key.

The identifiers that *would* make end-to-end linkage work are restricted:

| Identifier | What | Who has it | Public? |
|------------|------|------------|---------|
| **NYSID** | Statewide person ID (fingerprint-based) | DCJS, shared with OCA/courts/DOC/DOCCS | No |
| **CJTN** | Arrest-to-court transaction number | DCJS → court of arraignment | No |
| **Court docket / case #** | Court case identifier | OCA / courts | No (de-identified in bulk) |
| **INMATEID** | NYC DOC jail person ID | NYC DOC | **Yes** — the one we have |
| **DIN** | State prison person ID | DOCCS | Lookup only |

Key fact from Vera Institute research: NYC DOC does not record CJTN or arrest dates, so even researchers with restricted access had to match DOC to arrests by date logic.

### Current Join Quality

**DOC admissions ↔ discharges** — exact on `INMATEID`, strong. 97.7% match rate.

**Arrests ↔ complaints** — heuristic on date + precinct + offense code + borough, filtered by demographics. Results across 2.76M arrests (2014-2024):
- 34% unique match (good signal)
- 24% ambiguous (multiple complaints match)
- 34% no match
- Linkage quality is worse 2014-2017, better 2020-2024

**Arrests ↔ DOC admissions** — heuristic on date + sex + penal code + imputed age group. Current derived output: 12.4K unique matches (one admission to exactly one arrest). Covers 11.4K unique people, of which 904 have 2+ linked arrest-to-jail episodes. Narrow but clean — usable as a candidate bridge.

**Everything else** — not connected. No court outcomes, no cross-arrest person tracking.

### Cross-Source Join Surfaces

NYPD `LAW_CODE` (e.g. `PL 1552500`) can be parsed into penal law codes matching DOC `TOP_CHARGE` (e.g. `155.25`). Format: `PL XXXYYZZZ` → `XXX.YY`. 344 charges overlap. DOC `TOP_CHARGE` is only 38% non-null.

DOC discharge `AGE` + discharge date → approximate birth year (±1-2 years). This can be imputed back to admissions to compute expected NYPD age bucket at time of admission. Useful for tightening heuristic joins.

DOC race is useless for cross-source joins — only 3 values (BLACK, UNKNOWN, ASIAN) vs NYPD's 7 categories, with 43% UNKNOWN. DOC has no borough, no coordinates, no age on admissions.

### What Recidivism Tracking Requires

| Goal | Feasible now? | Size |
|------|--------------|------|
| DOC jail recidivism (repeat stays, gaps, charge patterns) | **Yes** — exact `INMATEID` | 86K repeat people, 250K readmission events |
| Linked arrest→jail episodes for a subset | **Candidate** — heuristic unique match | 12.4K episodes, 904 repeat people |
| Arrest-to-complaint linkage | Partial (~40%) | 1.1M linked of 2.8M arrests |
| Arrest-to-court-outcome | **No** — OCA extracts intentionally de-identified | — |
| Multi-arrest recidivism (same person, different arrests) | **No** — requires NYSID via DCJS agreement | — |
| Anything involving state prison | **No** — DOCCS only publishes aggregates | — |

## Tech Stack

| What | How |
|------|-----|
| Language | Python 3 |
| Data processing | Polars (lazy scans, expressions) |
| Canonical format | Parquet (derived); CSV (immutable raw inputs) |
| Package manager | uv |
| Optional | DuckDB for ad hoc queries |

## Key Commands

```bash
cd web && bun run dev                                    # Next.js explorer on localhost:3000
uv run python scripts/analyze_doc_recidivism.py         # person + episode recidivism
uv run python scripts/analyze_doc_cohort_recidivism.py  # time-bounded cohort rates
uv run python scripts/build_arrest_doc_bridge.py        # heuristic arrest-DOC linkage
uv run python scripts/build_public_event_panel.py --start-year 2014 --end-year 2024
uv run python scripts/build_public_event_spine_census_geo.py --year 2024
uv run python scripts/download_public_data.py           # fetch raw sources
```

Most build scripts accept `--year` or `--start-year / --end-year`. Add `--write-csv` only when you explicitly want a CSV export.

## Layout

| Path | Contents |
|------|----------|
| `scripts/` | All build, download, and analysis scripts |
| `data/raw/` | Immutable CSV downloads (git-ignored) |
| `data/derived/` | Parquet outputs (git-ignored) |
| `data/meta/` | Inventory JSON, profile JSON, coordinate cache (git-ignored) |
| `SOURCES.md` | Data source inventory with slugs, keys, joinability, and access notes |

The canonical research table is the multi-year census-enriched panel in `data/derived/`. Profile JSON in `data/meta/` has per-year coverage and quality signals.

## Architecture

```
raw CSV  -->  Polars lazy scan + clean + join  -->  Parquet (derived/)
                                                      |
                                               optional CSV export
```

Geocoding deduplicates unique coordinate pairs, caches in `data/meta/`, joins back. Avoids redundant Census API calls.

## Current Panel Stats (2014-2024)

- 10.6M rows, 31 columns, 241MB Parquet
- SEX: 99%, RACE: 96%, AGE_BUCKET: 92% coverage (NYPD sources)
- Census tract: 86-95% coverage (varies by year; DOC has 0% — no coordinates)
- DOC `INMATEID`: 197K unique people, 44% (86K) returned to jail 2+ times, 4.4K returned 10+ times
- Median DOC readmission gap: 182 days. 40K readmissions within 30 days.
- NYPD: zero person identifiers, zero recidivism capability

## Known Data Quality Issues

- DOC race categories (BLACK/UNKNOWN/ASIAN) don't map cleanly to NYPD categories (7 values). 43% DOC is UNKNOWN. Not useful for cross-source joins.
- DOC admissions have no age, no borough, no coordinates. `TOP_CHARGE` is only 38% non-null.
- Complaints `susp_age_group` is almost entirely standard buckets — only 279 out of 5.3M have raw integer ages (effectively zero, despite the panel showing 239 distinct `AGE_BUCKET` values from dirty data)
- Summonses have lower demographic coverage (~74% race, ~94% sex)
- YTD NYC Open Data feeds have historically lagged by a year

## Conventions

- Separate exact, candidate, and unsupported joins explicitly in code and output columns.
- Prefer Polars expressions and lazy scans over Python row loops.
- Start tiny when trying new joins — inspect actual matched rows before scaling.
- Keep raw data intact; never overwrite downloads.
- Commits stay small and source-only. Data files stay out of git.

## Boundaries

| | |
|---|---|
| **Always** | Inspect schema and sample rows before broad transforms; preserve raw copies; note quality issues |
| **Ask first** | Broad dependency additions, major restructuring, sending requests to nonpublic endpoints |
| **Never** | Fabricate joins, imply fuzzy matches are ground truth, overwrite raw downloads, create doc sprawl |
