import Link from "next/link";
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

      <section className="drose-panel">
        <div className="drose-section-header">
          <div>
            <p className="drose-kicker">High-Signal Profiles</p>
            <h2 className="drose-section-title">Top Recidivists</h2>
            <p className="drose-section-copy">
              People with the most jail admissions. Click any row for the full timeline,
              gap structure, linked arrests, and person-level history.
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
    </div>
  );
}
