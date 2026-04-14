# NYC CJ Explorer (`web/`)

Canonical web explorer for the `crims` research workspace. This app reads the
derived parquet outputs directly with DuckDB and is the primary dashboard now.
The old Streamlit app at the repo root is legacy/fallback only.

## Commands

Run the app locally:

```bash
cd web
bun run dev
```

Verify production health:

```bash
cd web
bun run lint
bun run build
```

For container deploys, the web app only needs these four files:

- `doc_recidivism_persons.parquet`
- `doc_recidivism_episodes.parquet`
- `doc_cohort_recidivism.parquet`
- `arrest_doc_bridge.parquet`

Mount them into the container and set `CRIMS_DATA_DIR` to that directory. The
bundled Docker image defaults to `/data/derived` and exposes `GET /health`.

For a subdirectory deploy such as `drose.io/nyc-crime`, set
`NEXT_PUBLIC_BASE_PATH=/nyc-crime` at build time and runtime. Public asset URLs
and the healthcheck follow that base path.

The app expects derived data under `../data/derived` relative to `web/`.
Generate or refresh those artifacts from the repo root before debugging empty
screens:

```bash
uv run python scripts/analyze_doc_recidivism.py
uv run python scripts/analyze_doc_cohort_recidivism.py
uv run python scripts/build_arrest_doc_bridge.py
```

## Routes

- `/` — top recidivists plus headline recidivism stats
- `/search` — URL-driven people search with filters
- `/person/[id]` — detailed person profile with timeline, episode chart, and bridge geography
- `/random-person` — redirect to a random high-repeat person

## Notes

- DuckDB native bindings are kept external via `serverExternalPackages`.
- `turbopack.root` is pinned in `next.config.ts` because this machine has other
  lockfiles outside the repo and Next otherwise infers the wrong workspace root.
- Leaflet marker assets are vendored in `public/leaflet/` so the map does not
  depend on a third-party CDN at runtime.

## Theme Layer

The current visual system is intentionally split into an extraction boundary so
the `drose.io` look can be reused elsewhere without another large refactor.

- `styles/drose-theme.css`
  - generated theme shell used by the app
  - imports shared token definitions plus the dark/void background system
- `styles/drose-core-tokens.css`
  - generated shared token layer
  - fonts, colors, shell sizing, motion, spacing, and shadow variables
- `styles/drose-primitives.css`
  - generated reusable surface primitives used by the app shell and pages
  - nav, hero, glass panel, stat card, button, form control, badge, and table
    treatments

These files are consumer copies of an external shared source-of-truth. Treat the
CSS classes and variables as the public API, but avoid hand-editing generated
copies unless you are intentionally breaking away from the shared theme.

## Stack

- Next.js App Router
- React 19
- Tailwind v4
- DuckDB via `@duckdb/node-api`
- Recharts
- Leaflet / react-leaflet
