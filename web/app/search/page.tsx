import { searchPersons, getSearchSummary, getFilterOptions } from "@/lib/queries";
import { TierBadge } from "@/components/tier-badge";
import { ClickableRow } from "@/components/clickable-row";
import { StatsCard } from "@/components/stats-card";
import { chargeLabel, formatDate } from "@/lib/format";
import type { SearchFilters } from "@/lib/types";
import { SearchFilterForm } from "./search-filters";

interface Props {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export const metadata = { title: "Search People — NYC CJ Explorer" };
const VALID_SORTS = new Set([
  "total_admissions",
  "first_admission",
  "last_admission",
  "avg_stay_days",
  "distinct_charges",
]);

export default async function SearchPage({ searchParams }: Props) {
  const sp = await searchParams;
  const rawSort = typeof sp.sort === "string" ? sp.sort : undefined;
  const filters: SearchFilters = {
    tier: typeof sp.tier === "string" ? sp.tier : undefined,
    race: typeof sp.race === "string" ? sp.race : undefined,
    sex: typeof sp.sex === "string" ? sp.sex : undefined,
    minAdmissions:
      typeof sp.min === "string" && /^[1-9]\d*$/.test(sp.min)
        ? Number(sp.min)
        : undefined,
    charge:
      typeof sp.charge === "string" && sp.charge.trim()
        ? sp.charge.trim()
        : undefined,
    sort: rawSort && VALID_SORTS.has(rawSort) ? rawSort : "total_admissions",
    dir: sp.dir === "asc" ? "asc" : "desc",
  };

  const [persons, summary, options] = await Promise.all([
    searchPersons(filters),
    getSearchSummary(filters),
    getFilterOptions(),
  ]);

  const repeatRate =
    summary.count > 0 ? summary.repeaters / summary.count : 0;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-gray-900">Search People</h1>

      <SearchFilterForm
        key={JSON.stringify(filters)}
        options={options}
        current={filters}
      />

      <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatsCard label="People" value={Number(summary.count).toLocaleString()} />
        <StatsCard
          label="Avg Admissions"
          value={summary.avg_admissions ? Number(summary.avg_admissions).toFixed(1) : "—"}
        />
        <StatsCard
          label="Repeat Rate"
          value={`${(repeatRate * 100).toFixed(1)}%`}
        />
      </div>

      <p className="mb-2 text-sm text-gray-500">
        Click any row to view details. Showing {persons.length}
        {summary.count > 500 ? ` of ${Number(summary.count).toLocaleString()}` : ""}.
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
            {persons.map((p) => (
              <ClickableRow key={p.INMATEID} href={`/person/${p.INMATEID}`} className="hover:bg-blue-50">
                <td className="px-3 py-2 font-medium text-blue-600">{p.INMATEID}</td>
                <td className="px-3 py-2 font-mono">{p.total_admissions}</td>
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
  );
}
