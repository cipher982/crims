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
uv run python scripts/build_doc_episode_dataset.py
uv run python scripts/build_arrest_research_dataset.py --year 2024
```

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

- `data/derived/doc_custody_episodes_joined.csv`
  - exact and candidate custody episode joins from DOC admissions + discharges
- `data/derived/nypd_arrests_2024_research_dataset.csv`
  - arrest-centered 2024 file with public identifiers, location fields, and complaint-link candidate status
