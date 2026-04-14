import { searchPersons, getSearchSummary, getFilterOptions } from "@/lib/queries";
import { ClickableRow } from "@/components/clickable-row";
import { chargeLabel, formatDate, tierLabel } from "@/lib/format";
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
    <div className="drose-page-stack">
      <section className="drose-hero drose-hero-compact">
        <p className="drose-kicker">Query The Public Dataset</p>
        <h1 className="drose-page-title">Search People</h1>
        <p className="drose-lead">
          Filter by recidivism tier, demographics, admissions, and charge code.
          Every view is URL-backed so the state stays shareable and restorable.
        </p>
      </section>

      <SearchFilterForm
        key={JSON.stringify(filters)}
        options={options}
        current={filters}
      />

      <p className="drose-summary-line">
        <strong>{Number(summary.count).toLocaleString()}</strong> people match
        the current filters. Average admissions are{" "}
        <strong>
          {summary.avg_admissions ? Number(summary.avg_admissions).toFixed(1) : "—"}
        </strong>{" "}
        and the repeat rate is <strong>{`${(repeatRate * 100).toFixed(1)}%`}</strong>.
      </p>

      <section className="drose-panel">
        <div className="drose-section-header">
          <div>
            <p className="drose-kicker">Result Set</p>
            <h2 className="drose-section-title">Matching People</h2>
            <p className="drose-section-copy">
              Click any row to view details. Showing {persons.length}
              {summary.count > 500
                ? ` of ${Number(summary.count).toLocaleString()}`
                : ""}.
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
            {persons.map((p) => (
              <ClickableRow key={p.INMATEID} href={`/person/${p.INMATEID}`}>
                <td className="drose-id-link">{p.INMATEID}</td>
                <td className="drose-mono">{p.total_admissions}</td>
                <td>{p.recidivism_tier ? tierLabel(p.recidivism_tier) : "—"}</td>
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
    </div>
  );
}
