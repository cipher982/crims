import { query, pq } from "./db";
import type {
  Person,
  Episode,
  BridgeRow,
  SearchFilters,
} from "./types";

const PERSONS = pq("doc_recidivism_persons.parquet");
const EPISODES = pq("doc_recidivism_episodes.parquet");
const COHORT = pq("doc_cohort_recidivism.parquet");
const BRIDGE = pq("arrest_doc_bridge.parquet");

// ---------------------------------------------------------------------------
// Landing page
// ---------------------------------------------------------------------------

export async function getOverviewStats() {
  const [persons, episodes, cohort] = await Promise.all([
    query<{ total: number; repeaters: number }>(
      `SELECT count(*) as total,
              count(*) FILTER (WHERE total_admissions > 1) as repeaters
       FROM '${PERSONS}'`
    ),
    query<{ total: number }>(
      `SELECT count(*) as total FROM '${EPISODES}'`
    ),
    query<{ eligible: number; returned: number }>(
      `SELECT count(*) FILTER (WHERE returned_1yr IS NOT NULL) as eligible,
              count(*) FILTER (WHERE returned_1yr = true) as returned
       FROM '${COHORT}'`
    ),
  ]);

  const p = persons[0];
  const e = episodes[0];
  const c = cohort[0];

  return {
    uniquePeople: p.total,
    jailEpisodes: e.total,
    repeatRate: p.total > 0 ? p.repeaters / p.total : 0,
    returnRate1yr: c.eligible > 0 ? c.returned / c.eligible : 0,
  };
}

export async function getAdmissionsByYear() {
  return query<{ year: number; count: number }>(
    `SELECT year(admit_date) as year, count(*) as count
     FROM '${EPISODES}'
     WHERE admit_date IS NOT NULL
     GROUP BY year
     ORDER BY year`
  );
}

export async function getReturnRateTrend() {
  return query<{ year: number; rate: number; n: number }>(
    `SELECT cohort_year as year,
            avg(returned_1yr::int)::double as rate,
            count(*) as n
     FROM '${COHORT}'
     WHERE returned_1yr IS NOT NULL
     GROUP BY cohort_year
     ORDER BY cohort_year`
  );
}

export async function getTopRecidivists(limit = 25) {
  return query<Person>(
    `SELECT * FROM '${PERSONS}'
     WHERE total_admissions > 1
     ORDER BY total_admissions DESC, last_admission DESC
     LIMIT ${limit}`
  );
}

// ---------------------------------------------------------------------------
// Person detail
// ---------------------------------------------------------------------------

export async function getPersonById(id: string): Promise<Person | null> {
  const rows = await query<Person>(
    `SELECT * FROM '${PERSONS}' WHERE INMATEID = '${id.replace(/'/g, "''")}'`
  );
  return rows[0] ?? null;
}

export async function getPersonEpisodes(id: string): Promise<Episode[]> {
  return query<Episode>(
    `SELECT * FROM '${EPISODES}'
     WHERE INMATEID = '${id.replace(/'/g, "''")}'
     ORDER BY admit_date`
  );
}

export async function getPersonBridge(id: string): Promise<BridgeRow[]> {
  return query<BridgeRow>(
    `SELECT * FROM '${BRIDGE}'
     WHERE INMATEID = '${id.replace(/'/g, "''")}'
     ORDER BY arrest_date`
  );
}

export async function getRandomHighRepeatId(): Promise<string | null> {
  const rows = await query<{ INMATEID: string }>(
    `SELECT INMATEID FROM '${PERSONS}'
     WHERE recidivism_tier = 'high_repeat'
     ORDER BY RANDOM()
     LIMIT 1`
  );
  return rows[0]?.INMATEID ?? null;
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export async function searchPersons(
  filters: SearchFilters,
  limit = 500
): Promise<Person[]> {
  const where = buildWhere(filters);
  const orderBy = buildOrderBy(filters);
  const safeLimit = clampLimit(limit);
  return query<Person>(
    `SELECT * FROM '${PERSONS}' ${where} ${orderBy} LIMIT ${safeLimit}`
  );
}

export async function getSearchSummary(filters: SearchFilters) {
  const where = buildWhere(filters);
  const rows = await query<{
    count: number;
    avg_admissions: number;
    repeaters: number;
  }>(
    `SELECT count(*) as count,
            avg(total_admissions)::double as avg_admissions,
            count(*) FILTER (WHERE total_admissions > 1) as repeaters
     FROM '${PERSONS}' ${where}`
  );
  return rows[0];
}

export async function getFilterOptions() {
  const [tiers, races, sexes] = await Promise.all([
    query<{ tier: string }>(
      `SELECT DISTINCT recidivism_tier as tier FROM '${PERSONS}' ORDER BY tier`
    ),
    query<{ race: string }>(
      `SELECT DISTINCT race FROM '${PERSONS}' WHERE race IS NOT NULL ORDER BY race`
    ),
    query<{ sex: string }>(
      `SELECT DISTINCT sex FROM '${PERSONS}' WHERE sex IS NOT NULL ORDER BY sex`
    ),
  ]);
  return {
    tiers: tiers.map((r) => r.tier),
    races: races.map((r) => r.race),
    sexes: sexes.map((r) => r.sex),
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildWhere(f: SearchFilters): string {
  const clauses: string[] = [];
  const tier = f.tier?.trim();
  const race = f.race?.trim();
  const sex = f.sex?.trim();
  const minAdmissions = normalizePositiveInt(f.minAdmissions);
  const charge = f.charge?.trim();

  if (tier) clauses.push(`recidivism_tier = '${escapeSqlLiteral(tier)}'`);
  if (race) clauses.push(`race = '${escapeSqlLiteral(race)}'`);
  if (sex) clauses.push(`sex = '${escapeSqlLiteral(sex)}'`);
  if (minAdmissions !== undefined)
    clauses.push(`total_admissions >= ${minAdmissions}`);
  if (charge)
    clauses.push(
      `first_known_charge IS NOT NULL AND first_known_charge ILIKE '%${escapeLike(charge)}%' ESCAPE '\\'`
    );
  return clauses.length > 0 ? "WHERE " + clauses.join(" AND ") : "";
}

function buildOrderBy(f: SearchFilters): string {
  const validCols = [
    "total_admissions",
    "recidivism_tier",
    "race",
    "first_admission",
    "last_admission",
    "avg_stay_days",
    "distinct_charges",
    "approx_birth_year",
  ];
  const col = validCols.includes(f.sort ?? "") ? f.sort! : "total_admissions";
  const dir = f.dir === "asc" ? "ASC" : "DESC";
  return `ORDER BY ${col} ${dir} NULLS LAST`;
}

function escapeSqlLiteral(value: string): string {
  return value.replace(/'/g, "''");
}

function escapeLike(value: string): string {
  return escapeSqlLiteral(value)
    .replace(/\\/g, "\\\\")
    .replace(/%/g, "\\%")
    .replace(/_/g, "\\_");
}

function normalizePositiveInt(value: number | undefined): number | undefined {
  if (value === undefined || !Number.isFinite(value)) {
    return undefined;
  }
  return Math.max(1, Math.trunc(value));
}

function clampLimit(value: number): number {
  if (!Number.isFinite(value)) {
    return 500;
  }
  return Math.max(1, Math.min(5000, Math.trunc(value)));
}
