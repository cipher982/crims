import { notFound } from "next/navigation";
import Link from "next/link";
import { getPersonById, getPersonEpisodes, getPersonBridge } from "@/lib/queries";
import { TierBadge } from "@/components/tier-badge";
import { chargeLabel, formatDate } from "@/lib/format";
import { PersonInsights } from "./person-insights";
import { JailTimeline } from "./jail-timeline";
import { EpisodeChart } from "./episode-chart";
import { EpisodesTable } from "./episodes-table";
import { ArrestMap } from "./arrest-map";

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props) {
  const { id } = await params;
  return { title: `Person ${id} — NYC CJ Explorer` };
}

export default async function PersonPage({ params }: Props) {
  const { id } = await params;

  const [person, episodes, bridge] = await Promise.all([
    getPersonById(id),
    getPersonEpisodes(id),
    getPersonBridge(id),
  ]);

  if (!person) notFound();

  const bridgePoints = bridge.filter(
    (b) => b.lat != null && b.lon != null && b.lat !== 0 && b.lon !== 0
  );

  return (
    <div className="drose-page-stack">
      <Link
        href="/search"
        className="drose-back-link"
      >
        &larr; Back to search
      </Link>

      <section className="drose-hero drose-hero-compact">
        <p className="drose-kicker">Person Profile</p>
        <div className="mb-3 flex flex-wrap items-center gap-3">
          <TierBadge tier={person.recidivism_tier} />
          <h1 className="drose-page-title">
            Person {person.INMATEID}
          </h1>
        </div>
        <p className="drose-lead">
          {person.total_admissions} admissions &middot;{" "}
          {person.race ?? "Unknown"} {person.sex ?? ""} &middot; b.
          ~{person.approx_birth_year ?? "?"}
        </p>
        <div className="drose-inline-meta">
          <span>
            <strong>First admission:</strong> {formatDate(person.first_admission)}
          </span>
          <span>
            <strong>Last admission:</strong> {formatDate(person.last_admission)}
          </span>
          {person.first_known_charge && (
            <span>
              <strong>First charge:</strong> {chargeLabel(person.first_known_charge)}
            </span>
          )}
          {person.last_known_charge && person.last_known_charge !== person.first_known_charge && (
            <span>
              <strong>Last charge:</strong> {chargeLabel(person.last_known_charge)}
            </span>
          )}
        </div>
      </section>

      <section>
        <PersonInsights person={person} episodes={episodes} />
      </section>

      <section>
        <JailTimeline episodes={episodes} />
      </section>

      <section>
        <EpisodeChart episodes={episodes} avgStay={person.avg_stay_days} />
      </section>

      {bridgePoints.length > 0 && (
        <section className="drose-panel overflow-hidden !p-0">
          <ArrestMap
            points={bridgePoints.map((b) => ({
              lat: b.lat!,
              lon: b.lon!,
              label: `${formatDate(b.arrest_date)} — ${chargeLabel(b.penal_code)} (${b.arrest_boro})`,
            }))}
          />
        </section>
      )}

      <section className="drose-panel">
        <div className="drose-section-header">
          <div>
            <p className="drose-kicker">Raw Episode History</p>
            <h2 className="drose-section-title">
              All Episodes ({episodes.length})
            </h2>
          </div>
        </div>
        <EpisodesTable episodes={episodes} />
      </section>

      {bridge.length > 0 && (
        <section className="drose-panel">
          <div className="drose-section-header">
            <div>
              <p className="drose-kicker">Candidate Linkage</p>
              <h2 className="drose-section-title">
                Linked Arrests ({bridge.length})
              </h2>
              <p className="drose-note">
                Heuristic arrest-DOC bridge matches. These are candidate links,
                not ground truth.
              </p>
            </div>
          </div>
          <div className="drose-table-wrap">
            <table className="drose-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Boro</th>
                  <th>Precinct</th>
                  <th>Charge</th>
                  <th>Category</th>
                  <th>Race</th>
                  <th>Sex</th>
                </tr>
              </thead>
              <tbody>
                {bridge.map((b) => (
                  <tr key={b.ARREST_KEY}>
                    <td className="drose-mono">{formatDate(b.arrest_date)}</td>
                    <td>{b.arrest_boro ?? "—"}</td>
                    <td>{b.arrest_precinct ?? "—"}</td>
                    <td>{chargeLabel(b.penal_code)}</td>
                    <td>{b.law_category ?? "—"}</td>
                    <td>{b.arrest_race ?? "—"}</td>
                    <td>{b.arrest_sex ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
