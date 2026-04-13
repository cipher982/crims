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
    <div>
      {/* Header with key stats inline */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          NYC Criminal Justice Explorer
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          {Number(stats.uniquePeople).toLocaleString()} people
          {" · "}
          {Number(stats.jailEpisodes).toLocaleString()} jail episodes
          {" · "}
          {(stats.repeatRate * 100).toFixed(1)}% returned 2+ times
          {" · "}
          {(stats.returnRate1yr * 100).toFixed(1)}% returned within 1 year
        </p>
      </div>

      {/* Action buttons */}
      <div className="mb-6 flex gap-3">
        <Link
          href="/search"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Search All People
        </Link>
        <Link
          href="/random-person"
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Random Person
        </Link>
      </div>

      {/* Top recidivists table — the hero */}
      <div className="mb-8">
        <h2 className="mb-3 text-lg font-semibold text-gray-900">
          Top Recidivists
        </h2>
        <p className="mb-2 text-sm text-gray-500">
          People with the most jail admissions. Click any row for full profile.
        </p>
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-gray-500">INMATEID</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Admissions</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Tier</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Race</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Sex</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Birth Year</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">First Admission</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Last Admission</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">Avg Stay</th>
                <th className="px-3 py-2 text-left font-medium text-gray-500">First Charge</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-800">
              {topPeople.map((p) => (
                <ClickableRow key={p.INMATEID} href={`/person/${p.INMATEID}`} className="hover:bg-blue-50">
                  <td className="px-3 py-2 font-medium text-blue-600">{p.INMATEID}</td>
                  <td className="px-3 py-2 font-mono font-semibold">{p.total_admissions}</td>
                  <td className="px-3 py-2"><TierBadge tier={p.recidivism_tier} /></td>
                  <td className="px-3 py-2">{p.race ?? "—"}</td>
                  <td className="px-3 py-2">{p.sex ?? "—"}</td>
                  <td className="px-3 py-2">{p.approx_birth_year ?? "—"}</td>
                  <td className="px-3 py-2 font-mono">{formatDate(p.first_admission)}</td>
                  <td className="px-3 py-2 font-mono">{formatDate(p.last_admission)}</td>
                  <td className="px-3 py-2">
                    {p.avg_stay_days != null
                      ? `${Math.round(Number(p.avg_stay_days))}d`
                      : "—"}
                  </td>
                  <td className="px-3 py-2">{chargeLabel(p.first_known_charge)}</td>
                </ClickableRow>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts — secondary, below the fold */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <SimpleBarChart data={admData} title="Admissions by Year" />
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <SimpleLineChart
            data={trendData}
            title="1-Year Return Rate"
            color="#ef4444"
            pct
          />
        </div>
      </div>
    </div>
  );
}
