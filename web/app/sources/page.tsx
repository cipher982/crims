import { connection } from "next/server";
import Link from "next/link";
import { MethodBadge } from "@/components/method-badge";
import { formatNumber } from "@/lib/format";
import {
  CURRENT_APP_DATASETS,
  CURRENT_APP_SOURCES,
  DOCUMENTED_NOT_YET_SURFACED,
  JOIN_ROWS,
  REPO_PANEL_SOURCES,
  getOptionalPanelProfile,
} from "@/lib/research";

export const metadata = { title: "Sources - NYC CJ Explorer" };

export default async function SourcesPage() {
  await connection();
  const panelProfile = await getOptionalPanelProfile();

  return (
    <div className="drose-page-stack">
      <section className="drose-hero drose-hero-compact">
        <p className="drose-kicker">Sources</p>
        <h1 className="drose-page-title">Public data behind the explorer</h1>
        <p className="drose-lead">
          The site is built from public NYC open-data releases plus a small
          amount of public census geography enrichment. This page separates
          sources that power the live app from the wider research inventory
          documented in the repo.
        </p>
        <div className="drose-actions">
          <Link href="/methodology" className="drose-button drose-button-secondary">
            Read Methods
          </Link>
          <Link href="/search" className="drose-button drose-button-primary">
            Explore People
          </Link>
        </div>
      </section>

      <section className="drose-panel">
        <div className="drose-section-header">
          <div>
            <p className="drose-kicker">Current Web App Inputs</p>
            <h2 className="drose-section-title">Sources actively surfaced in the live routes</h2>
            <p className="drose-section-copy">
              These are the public inputs that directly feed the four Parquet
              files consumed by the web app.
            </p>
          </div>
        </div>
        <div className="drose-table-wrap">
          <table className="drose-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Agency</th>
                <th>Dataset</th>
                <th>Coverage</th>
                <th>Grain</th>
                <th>Key</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {CURRENT_APP_SOURCES.map((row) => (
                <tr key={row.source}>
                  <td>{row.source}</td>
                  <td>{row.agency}</td>
                  <td className="drose-mono">{row.dataset}</td>
                  <td>{row.coverage}</td>
                  <td>{row.grain}</td>
                  <td className="drose-mono">{row.key}</td>
                  <td>{row.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Current App Outputs</p>
              <h2 className="drose-section-title">Derived datasets the site reads</h2>
              <p className="drose-section-copy">
                The web app reads Parquet directly through DuckDB. Each file
                below has a specific role and confidence grade.
              </p>
            </div>
          </div>
          <div className="space-y-3">
            {CURRENT_APP_DATASETS.map((dataset) => (
              <div
                key={dataset.name}
                className="rounded-2xl border border-white/8 bg-white/4 p-4"
              >
                <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
                  <p className="m-0 font-mono text-sm text-[var(--drose-text)]">
                    {dataset.name}
                  </p>
                  <MethodBadge status={dataset.confidence} />
                </div>
                <p className="m-0 text-sm leading-7 text-[var(--drose-text-muted)]">
                  {dataset.method}
                </p>
                <p className="mt-2 text-xs uppercase tracking-[0.12em] text-[var(--drose-text-secondary)]">
                  Built by {dataset.builtBy}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Repo Panel Inputs</p>
              <h2 className="drose-section-title">Broader public event graph sources</h2>
              <p className="drose-section-copy">
                These sources are part of the wider research workspace, even
                when they are not all surfaced on the current routes.
              </p>
            </div>
          </div>
          <div className="drose-table-wrap">
            <table className="drose-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Dataset</th>
                  <th>Coverage</th>
                  <th>Key</th>
                  <th>Role</th>
                </tr>
              </thead>
              <tbody>
                {REPO_PANEL_SOURCES.map((row) => (
                  <tr key={row.source}>
                    <td>{row.source}</td>
                    <td className="drose-mono">{row.dataset}</td>
                    <td>{row.coverage}</td>
                    <td className="drose-mono">{row.key}</td>
                    <td>{row.role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {panelProfile && (
            <p className="drose-note">
              Local profile currently available: {formatNumber(panelProfile.total_rows)}
              {` `}rows in the 2014-2024 public event panel.
            </p>
          )}
        </div>
      </section>

      <section className="drose-panel">
        <div className="drose-section-header">
          <div>
            <p className="drose-kicker">Join Surfaces</p>
            <h2 className="drose-section-title">How sources touch each other</h2>
            <p className="drose-section-copy">
              A source being public does not mean it is joinable. The limiting
              factor is whether the released fields expose a defensible path
              from one stage to another.
            </p>
          </div>
        </div>
        <div className="drose-table-wrap">
          <table className="drose-table">
            <thead>
              <tr>
                <th>Join</th>
                <th>Fields</th>
                <th>Status</th>
                <th>Supports</th>
                <th>Caveat</th>
              </tr>
            </thead>
            <tbody>
              {JOIN_ROWS.map((row) => (
                <tr key={row.join}>
                  <td>{row.join}</td>
                  <td className="drose-mono">{row.fields}</td>
                  <td>
                    <MethodBadge status={row.status} />
                  </td>
                  <td>{row.supports}</td>
                  <td>{row.caveat}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="drose-panel">
        <div className="drose-section-header">
          <div>
            <p className="drose-kicker">Documented Inventory</p>
            <h2 className="drose-section-title">Public sources tracked in the repo but not yet surfaced here</h2>
            <p className="drose-section-copy">
              These sources are documented because they matter for the broader
              research path, but they are not currently powering the live
              explorer routes.
            </p>
          </div>
        </div>
        <div className="drose-table-wrap">
          <table className="drose-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Agency</th>
                <th>Dataset</th>
                <th>Coverage</th>
                <th>Key</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {DOCUMENTED_NOT_YET_SURFACED.map((row) => (
                <tr key={row.source}>
                  <td>{row.source}</td>
                  <td>{row.agency}</td>
                  <td className="drose-mono">{row.dataset}</td>
                  <td>{row.coverage}</td>
                  <td className="drose-mono">{row.key}</td>
                  <td>{row.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
