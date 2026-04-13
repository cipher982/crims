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
    <div>
      <Link
        href="/search"
        className="mb-4 inline-block text-sm text-blue-600 hover:text-blue-800"
      >
        &larr; Back to search
      </Link>

      {/* Profile header */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6">
        <div className="flex items-center gap-3 mb-2">
          <TierBadge tier={person.recidivism_tier} />
          <h1 className="text-xl font-bold text-gray-900">
            Person {person.INMATEID}
          </h1>
        </div>
        <p className="text-gray-600">
          {person.total_admissions} admissions &middot;{" "}
          {person.race ?? "Unknown"} {person.sex ?? ""} &middot; b.
          ~{person.approx_birth_year ?? "?"}
        </p>
        <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-500">
          <span>
            First admission: <span className="text-gray-700">{formatDate(person.first_admission)}</span>
          </span>
          <span>
            Last admission: <span className="text-gray-700">{formatDate(person.last_admission)}</span>
          </span>
          {person.first_known_charge && (
            <span>
              First charge: <span className="text-gray-700">{chargeLabel(person.first_known_charge)}</span>
            </span>
          )}
          {person.last_known_charge && person.last_known_charge !== person.first_known_charge && (
            <span>
              Last charge: <span className="text-gray-700">{chargeLabel(person.last_known_charge)}</span>
            </span>
          )}
        </div>
      </div>

      {/* Key insights — the high-signal numbers */}
      <div className="mb-6">
        <PersonInsights person={person} episodes={episodes} />
      </div>

      {/* Incarceration timeline — the duty cycle */}
      <div className="mb-6">
        <JailTimeline episodes={episodes} />
      </div>

      {/* Episode breakdown — stay durations + gaps stacked */}
      <div className="mb-6">
        <EpisodeChart episodes={episodes} avgStay={person.avg_stay_days} />
      </div>

      {/* Arrest geography */}
      {bridgePoints.length > 0 && (
        <div className="mb-6 rounded-lg border border-gray-200 overflow-hidden">
          <ArrestMap
            points={bridgePoints.map((b) => ({
              lat: b.lat!,
              lon: b.lon!,
              label: `${formatDate(b.arrest_date)} — ${chargeLabel(b.penal_code)} (${b.arrest_boro})`,
            }))}
          />
        </div>
      )}

      {/* Episodes table — the raw data, collapsed by default feel */}
      <div className="mb-6">
        <h2 className="mb-3 text-lg font-semibold text-gray-900">
          All Episodes ({episodes.length})
        </h2>
        <EpisodesTable episodes={episodes} />
      </div>

      {/* Bridge arrest table */}
      {bridge.length > 0 && (
        <div className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-gray-900">
            Linked Arrests ({bridge.length})
          </h2>
          <p className="mb-2 text-xs text-gray-400">
            Heuristic arrest-DOC bridge matches — candidate links, not ground truth
          </p>
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Date</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Boro</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Precinct</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Charge</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Category</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Race</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Sex</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-800">
                {bridge.map((b) => (
                  <tr key={b.ARREST_KEY} className="hover:bg-blue-50">
                    <td className="px-3 py-2 font-mono">{formatDate(b.arrest_date)}</td>
                    <td className="px-3 py-2">{b.arrest_boro ?? "—"}</td>
                    <td className="px-3 py-2">{b.arrest_precinct ?? "—"}</td>
                    <td className="px-3 py-2">{chargeLabel(b.penal_code)}</td>
                    <td className="px-3 py-2">{b.law_category ?? "—"}</td>
                    <td className="px-3 py-2">{b.arrest_race ?? "—"}</td>
                    <td className="px-3 py-2">{b.arrest_sex ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
