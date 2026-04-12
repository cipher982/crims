# AGENTS.md

## Project Overview

**crims** is a lean research workspace for assembling the best possible public NYC criminal-justice dataset, understanding what can be joined, and identifying where public access stops.

## Tech Stack

| Category | Technology |
| --- | --- |
| Language(s) | Python 3 |
| Framework(s) | none |
| Database(s) | local flat files first; optional DuckDB for analysis |
| Key dependencies | stdlib first; add analysis deps only when they unlock clear value |

## Build & Test

| Action | Command |
| --- | --- |
| Run exploration file | `uv run python scripts/public_mvp.py` |
| Run a one-off Python check | `uv run python -c "..."` |
| List raw data | `find data -maxdepth 2 -type f | sort` |

## Architecture Overview

This repo should stay simple. The core flow is:

1. acquire raw public datasets locally
2. inspect heads, keys, nulls, and date coverage
3. test one join at a time
4. keep exact joins separate from heuristic joins
5. document what is trustworthy and what is not

Prefer notebook-style exploration over early pipeline design.

## Working Vision

- Build the best public raw dataset we can without pretending public records support a full named person graph.
- Treat this as an `event graph` first: arrests, complaints, summonses, jail admissions, jail discharges, daily custody snapshots.
- Use restricted-data planning only after the public path is exhausted.

## Success Criteria

Today’s strong outcome:

- primary public datasets downloaded locally
- row counts, date coverage, and key fields verified
- one exact join working on local data
- one heuristic cross-stage join explored with ambiguity measured
- findings written down tightly, without doc sprawl

## Conventions

- Keep notes in as few files as possible.
- Prefer visible, incremental exploration to large opaque scripts.
- When trying joins, start tiny and inspect actual matched rows.
- Separate `exact`, `candidate`, and `unsupported` joins explicitly.
- Flag stale or suspicious feeds immediately.

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

- This workspace may not be a git repo yet.
- If git is initialized later, keep commits small and data files out of version control unless explicitly requested.

## Updating This File

Update this file when the workflow changes, when a join rule proves brittle, or when a better success criterion becomes obvious from the data.
