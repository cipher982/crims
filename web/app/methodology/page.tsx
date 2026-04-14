import Link from "next/link";
import { MethodBadge } from "@/components/method-badge";
import { StatsCard } from "@/components/stats-card";
import { formatNumber } from "@/lib/format";
import { getMethodStats } from "@/lib/queries";
import {
  BUILD_STEPS,
  BROADER_REPO_DATASETS,
  CURRENT_APP_DATASETS,
  JOIN_ROWS,
  NON_CLAIMS,
  getOptionalPanelProfile,
} from "@/lib/research";

export const metadata = { title: "Methodology - NYC CJ Explorer" };
export const dynamic = "force-dynamic";

export default async function MethodologyPage() {
  const [stats, panelProfile] = await Promise.all([
    getMethodStats(),
    getOptionalPanelProfile(),
  ]);

  return (
    <div className="drose-page-stack">
      <section className="drose-hero drose-hero-compact">
        <p className="drose-kicker">Methods</p>
        <h1 className="drose-page-title">How the explorer is built</h1>
        <p className="drose-lead">
          The site is deliberately strict about what it claims. Exact DOC jail
          histories are shown as exact. Arrest-to-jail links are labeled as
          candidate. Court and prison linkage are kept out unless the public
          data can actually support them.
        </p>
        <div className="drose-actions">
          <Link href="/sources" className="drose-button drose-button-secondary">
            View Sources
          </Link>
          <Link href="/search" className="drose-button drose-button-primary">
            Explore People
          </Link>
        </div>
      </section>

      <div className="drose-stat-grid">
        <StatsCard
          label="Exact DOC People"
          value={formatNumber(stats.uniquePeople)}
        />
        <StatsCard
          label="Repeat Admissions"
          value={`${formatNumber(stats.repeatPeople)} (${(stats.repeatRate * 100).toFixed(1)}%)`}
        />
        <StatsCard
          label="Median Readmission Gap"
          value={stats.medianGapDays != null ? `${Math.round(stats.medianGapDays)}d` : "—"}
        />
      </div>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Truth Standard</p>
              <h2 className="drose-section-title">What the app can claim</h2>
              <p className="drose-section-copy">
                The unit of confidence is the join, not the visualization. Every
                route in the app inherits the confidence of the underlying
                linkage.
              </p>
            </div>
          </div>
          <div className="grid gap-3">
            <div className="rounded-2xl border border-cyan-400/15 bg-cyan-400/6 p-4">
              <div className="mb-2">
                <MethodBadge status="exact" />
              </div>
              <p className="m-0 text-sm leading-7 text-[var(--drose-text-muted)]">
                DOC admissions and discharges join on <code>INMATEID + admit_date</code>,
                which supports exact jail episode histories, repeat-admission
                counts, and cohort return metrics.
              </p>
            </div>
            <div className="rounded-2xl border border-amber-400/15 bg-amber-400/6 p-4">
              <div className="mb-2">
                <MethodBadge status="candidate" />
              </div>
              <p className="m-0 text-sm leading-7 text-[var(--drose-text-muted)]">
                The arrest bridge keeps only unique 1:1 matches after filtering
                on same date, normalized sex, parsed penal code, and compatible
                age bucket.
              </p>
            </div>
            <div className="rounded-2xl border border-rose-400/15 bg-rose-400/6 p-4">
              <div className="mb-2">
                <MethodBadge status="unsupported" />
              </div>
              <p className="m-0 text-sm leading-7 text-[var(--drose-text-muted)]">
                Public court bulk extracts are de-identified and public prison
                releases are aggregate, so this site does not claim full
                cross-stage identity resolution.
              </p>
            </div>
          </div>
        </div>

        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Current Runtime</p>
              <h2 className="drose-section-title">What the live app reads</h2>
              <p className="drose-section-copy">
                The deployed explorer is intentionally narrow. It only needs the
                four derived Parquet files below, all built from public inputs.
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
                  {dataset.grain} · {dataset.usedFor}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="drose-panel">
        <div className="drose-section-header">
          <div>
            <p className="drose-kicker">Build Chain</p>
            <h2 className="drose-section-title">Pipeline steps</h2>
            <p className="drose-section-copy">
              Each step writes a concrete artifact. The app does not synthesize
              methods at runtime; it reads the outputs of these build scripts.
            </p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {BUILD_STEPS.map((step) => (
            <div
              key={step.script}
              className="rounded-2xl border border-white/8 bg-white/4 p-4"
            >
              <p className="m-0 font-mono text-sm text-[var(--drose-text)]">
                {step.script}
              </p>
              <p className="mt-2 text-sm leading-7 text-[var(--drose-text-muted)]">
                {step.purpose}
              </p>
              <p className="mt-3 text-xs uppercase tracking-[0.12em] text-[var(--drose-text-secondary)]">
                Outputs: {step.outputs}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="drose-panel">
        <div className="drose-section-header">
          <div>
            <p className="drose-kicker">Join Quality</p>
            <h2 className="drose-section-title">What is exact, candidate, or unsupported</h2>
            <p className="drose-section-copy">
              This is the core methodological boundary of the project. Public
              criminal-justice data is mostly event-level. Only some layers can
              be stitched into person histories without inventing certainty.
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

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_1fr]">
        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Bridge Method</p>
              <h2 className="drose-section-title">How arrests are linked to DOC</h2>
              <p className="drose-section-copy">
                The bridge is intentionally narrow. Coverage is sacrificed to
                reduce obvious false positives.
              </p>
            </div>
          </div>
          <ol className="m-0 space-y-3 pl-5 text-sm leading-7 text-[var(--drose-text-muted)]">
            <li>Parse NYPD <code>LAW_CODE</code> into a penal-law format that can match DOC <code>TOP_CHARGE</code>.</li>
            <li>Require the arrest date to equal the DOC admission date.</li>
            <li>Require normalized sex to agree across systems.</li>
            <li>Use discharge-age-derived birth year to infer the expected NYPD age bucket.</li>
            <li>Keep only rows that survive as unique 1:1 arrest-to-admission matches.</li>
          </ol>
          <p className="drose-note">
            Current build: {formatNumber(stats.bridgeMatches)} candidate pairs,
            {` ${formatNumber(stats.bridgePeople)} `}unique DOC people, and{` `}
            {formatNumber(stats.repeatBridgePeople)} people with 2+ linked
            episodes.
          </p>
        </div>

        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Non-Claims</p>
              <h2 className="drose-section-title">What the site does not assert</h2>
              <p className="drose-section-copy">
                These are not small footnotes. They define the ceiling of what a
                public-only NYC criminal-justice explorer can truthfully say.
              </p>
            </div>
          </div>
          <ul className="m-0 space-y-3 pl-5 text-sm leading-7 text-[var(--drose-text-muted)]">
            {NON_CLAIMS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_1fr]">
        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Broader Repo Outputs</p>
              <h2 className="drose-section-title">Additional datasets in the workspace</h2>
              <p className="drose-section-copy">
                The repo builds more than the live explorer currently exposes.
                Those outputs stay labeled by their own confidence level.
              </p>
            </div>
          </div>
          <div className="space-y-3">
            {BROADER_REPO_DATASETS.map((dataset) => (
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
              </div>
            ))}
          </div>
        </div>

        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Live Build Notes</p>
              <h2 className="drose-section-title">Numbers on this page</h2>
              <p className="drose-section-copy">
                These values are pulled from current derived outputs so the
                methods copy stays in sync with the latest local build.
              </p>
            </div>
          </div>
          <div className="space-y-3 text-sm leading-7 text-[var(--drose-text-muted)]">
            <p className="m-0">
              Exact DOC layer: {formatNumber(stats.uniquePeople)} people,{` `}
              {formatNumber(stats.jailEpisodes)} jail episodes, max{` `}
              {formatNumber(stats.maxAdmissions)} admissions for a single
              person, and a {(stats.returnRate1yr * 100).toFixed(1)}% 1-year
              return rate among observable cohorts.
            </p>
            {panelProfile ? (
              <p className="m-0">
                Local panel profile available: {formatNumber(panelProfile.total_rows)}
                {` `}rows in the 2014-2024 public event panel.
              </p>
            ) : (
              <p className="m-0">
                The broader event panel is optional at runtime, so this page
                does not require those larger files to be deployed.
              </p>
            )}
            <p className="m-0">
              The website itself still reads only the narrow set of current app
              Parquet outputs. The broader repo outputs are documented here so
              the methodology stays honest about what exists versus what is
              actually surfaced.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
