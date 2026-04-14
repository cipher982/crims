import Link from "next/link";
import { MethodBadge } from "@/components/method-badge";
import { TierBadge } from "@/components/tier-badge";
import { ClickableRow } from "@/components/clickable-row";
import { SimpleBarChart } from "@/components/charts/bar-chart";
import { SimpleLineChart } from "@/components/charts/line-chart";
import {
  getOverviewStats,
  getAdmissionsByYear,
  getReturnRateTrend,
  getTopRecidivists,
} from "@/lib/queries";
import { chargeLabel, formatDate } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [stats, admissions, trend, topPeople] = await Promise.all([
    getOverviewStats(),
    getAdmissionsByYear(),
    getReturnRateTrend(),
    getTopRecidivists(25),
  ]);

  const admData = admissions.map((r) => ({
    name: String(r.year),
    value: Number(r.count),
  }));

  const trendData = trend.map((r) => ({
    name: String(r.year),
    value: Number(r.rate),
  }));

  return (
    <div className="drose-page-stack">
      <section className="drose-hero">
        <p className="drose-kicker">Public NYC DOC Research Explorer</p>
        <h1 className="drose-hero-title">NYC Criminal Justice Explorer</h1>
        <p className="drose-lead">
          Person-centric exploration of NYC DOC admissions, repeat incarceration,
          charge patterns, and the cleanest public arrest-to-jail bridge subset.
        </p>

        <div className="drose-metric-row">
          <span className="drose-metric-chip">
            <strong>{Number(stats.uniquePeople).toLocaleString()}</strong> people
          </span>
          <span className="drose-metric-chip">
            <strong>{Number(stats.jailEpisodes).toLocaleString()}</strong> jail episodes
          </span>
          <span className="drose-metric-chip">
            <strong>{(stats.repeatRate * 100).toFixed(1)}%</strong> returned 2+ times
          </span>
          <span className="drose-metric-chip">
            <strong>{(stats.returnRate1yr * 100).toFixed(1)}%</strong> within 1 year
          </span>
        </div>

        <div className="drose-actions">
          <Link href="/search" className="drose-button drose-button-primary">
            Search All People
          </Link>
          <Link
            href="/random-person"
            className="drose-button drose-button-secondary"
          >
            Random Person
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">How To Read This Explorer</p>
              <h2 className="drose-section-title">What is exact and what is not</h2>
              <p className="drose-section-copy">
                The site centers exact NYC DOC jail histories. Arrest context is
                narrower and appears only when the public data supports a
                candidate bridge.
              </p>
            </div>
          </div>
          <div className="drose-doc-list">
            <div className="drose-doc-item">
              <p className="drose-doc-item-title">
                <MethodBadge status="exact" />
                Exact DOC histories
              </p>
              <p className="drose-doc-item-copy">
                DOC person pages, episode counts, stay lengths, gap lengths, and
                cohort return rates all come from exact joins inside the public
                DOC feeds.
              </p>
            </div>
            <div className="drose-doc-item">
              <p className="drose-doc-item-title">
                <MethodBadge status="candidate" />
                Candidate arrest context
              </p>
              <p className="drose-doc-item-copy">
                Arrest rows and map points are candidate matches only. They come
                from a strict 1:1 bridge, not a full cross-system person key.
              </p>
            </div>
            <div className="drose-doc-item">
              <p className="drose-doc-item-title">
                <MethodBadge status="unsupported" />
                Unsupported claims
              </p>
              <p className="drose-doc-item-copy">
                Court outcomes, prison histories, parole, and citywide
                multi-arrest identity resolution remain outside what public bulk
                data can support here.
              </p>
            </div>
          </div>
        </div>

        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Methods + Sources</p>
              <h2 className="drose-section-title">What the app is built from</h2>
              <p className="drose-section-copy">
                The current web app reads four derived Parquet outputs built from
                public NYC DOC and NYPD data. The broader repo also carries a
                larger public event panel for research work outside these routes.
              </p>
            </div>
          </div>
          <div className="space-y-3 text-sm leading-7 text-[var(--drose-text-muted)]">
            <p className="m-0">
              Core runtime inputs: DOC admissions, DOC discharges, DOC cohort
              outcomes, and the candidate arrest-DOC bridge.
            </p>
            <p className="m-0">
              Broader repo inputs: NYPD complaints, arrests, summonses, and
              Census geography enrichment for the multi-year public event panel.
            </p>
            <p className="m-0">
              The detailed build notes now live on dedicated site pages so the
              methodology stays visible instead of buried in repo docs.
            </p>
          </div>
          <div className="drose-actions">
            <Link href="/methodology" className="drose-button drose-button-primary">
              Read Methodology
            </Link>
            <Link href="/sources" className="drose-button drose-button-secondary">
              Browse Sources
            </Link>
          </div>
        </div>
      </section>

      <section className="drose-panel">
        <div className="drose-section-header">
          <div>
            <p className="drose-kicker">High-Signal Profiles</p>
            <h2 className="drose-section-title">Top Recidivists</h2>
            <p className="drose-section-copy">
              People with the most jail admissions. Click any row for the full timeline,
              gap structure, linked arrests, and person-level history. The person
              identity here is exact within DOC. Any linked arrests you see later
              are candidate bridge matches, not ground-truth cross-system IDs.
            </p>
          </div>
        </div>

        <div className="drose-table-wrap">
          <table className="drose-table">
            <thead>
              <tr>
                <th>INMATEID</th>
                <th>Admissions</th>
                <th>Tier</th>
                <th>Race</th>
                <th>Sex</th>
                <th>Birth Year</th>
                <th>First Admission</th>
                <th>Last Admission</th>
                <th>Avg Stay</th>
                <th>First Charge</th>
              </tr>
            </thead>
            <tbody>
              {topPeople.map((p) => (
                <ClickableRow key={p.INMATEID} href={`/person/${p.INMATEID}`}>
                  <td className="drose-id-link">{p.INMATEID}</td>
                  <td className="drose-mono font-semibold">{p.total_admissions}</td>
                  <td><TierBadge tier={p.recidivism_tier} /></td>
                  <td>{p.race ?? "—"}</td>
                  <td>{p.sex ?? "—"}</td>
                  <td>{p.approx_birth_year ?? "—"}</td>
                  <td className="drose-mono">{formatDate(p.first_admission)}</td>
                  <td className="drose-mono">{formatDate(p.last_admission)}</td>
                  <td>
                    {p.avg_stay_days != null
                      ? `${Math.round(Number(p.avg_stay_days))}d`
                      : "—"}
                  </td>
                  <td>{chargeLabel(p.first_known_charge)}</td>
                </ClickableRow>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="drose-panel">
          <SimpleBarChart data={admData} title="Admissions by Year" />
        </div>
        <div className="drose-panel">
          <SimpleLineChart
            data={trendData}
            title="1-Year Return Rate"
            color="#ec4899"
            pct
          />
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Scope</p>
              <h2 className="drose-section-title">What this site covers well</h2>
            </div>
          </div>
          <p className="drose-panel-copy">
            Exact DOC repeat-admission histories, timing between jail episodes,
            cohort return rates, and a narrow arrest-to-jail bridge subset where
            the public fields line up cleanly enough to keep only unique 1:1
            matches.
          </p>
        </div>
        <div className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Limits</p>
              <h2 className="drose-section-title">What public data still cannot do</h2>
            </div>
          </div>
          <p className="drose-panel-copy">
            This explorer does not claim court outcomes, prison histories,
            parole, or true multi-arrest person resolution across the full NYC
            criminal-justice pipeline. Those require restricted identifiers that
            are not exposed in public bulk releases.
          </p>
        </div>
      </section>
    </div>
  );
}
