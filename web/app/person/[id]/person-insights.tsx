import type { Person, Episode } from "@/lib/types";
import { chargeLabel } from "@/lib/format";

interface Props {
  person: Person;
  episodes: Episode[];
}

export function PersonInsights({ person, episodes }: Props) {
  const stats = computeInsights(person, episodes);
  if (!stats) return null;

  return (
    <div className="drose-stat-grid drose-person-stat-grid">
      {stats.map((s) => (
        <div key={s.label} className="drose-stat-card">
          <div className="drose-stat-value">{s.value}</div>
          <div className="drose-stat-label">{s.label}</div>
          {s.detail && (
            <div className="drose-stat-detail">{s.detail}</div>
          )}
        </div>
      ))}
    </div>
  );
}

type Stat = { label: string; value: string; detail?: string };

function computeInsights(person: Person, episodes: Episode[]): Stat[] | null {
  if (episodes.length === 0) return null;

  const stats: Stat[] = [];

  // 1. Total jail time
  const totalStay = episodes.reduce((s, e) => s + Number(e.stay_days ?? 0), 0);
  if (totalStay > 365) {
    const years = (totalStay / 365).toFixed(1);
    stats.push({
      label: "Total time in jail",
      value: `${years} yrs`,
      detail: `${totalStay.toLocaleString()} days across ${episodes.length} stays`,
    });
  } else {
    stats.push({
      label: "Total time in jail",
      value: `${totalStay}d`,
      detail: `${episodes.length} stays`,
    });
  }

  // 2. % of tracked time incarcerated
  const firstAdmit = new Date(person.first_admission);
  const lastDate = person.last_discharge
    ? new Date(person.last_discharge)
    : new Date(person.last_admission);
  const spanDays = Math.max(
    1,
    Math.round((lastDate.getTime() - firstAdmit.getTime()) / 86400000)
  );
  const pctJail = Math.min(100, (totalStay / spanDays) * 100);
  stats.push({
    label: "Time incarcerated",
    value: `${pctJail.toFixed(0)}%`,
    detail: `of ${(spanDays / 365).toFixed(1)} year span`,
  });

  // 3. Fastest return
  const gaps = episodes
    .map((e) => (e.gap_days != null ? Number(e.gap_days) : null))
    .filter((g): g is number => g != null && g > 0);
  if (gaps.length > 0) {
    const fastest = Math.min(...gaps);
    stats.push({
      label: "Fastest return",
      value: `${fastest}d`,
      detail:
        fastest <= 7
          ? "Within a week"
          : fastest <= 30
            ? "Within a month"
            : fastest <= 365
              ? "Within a year"
              : undefined,
    });
  }

  // 4. Distinct charges
  const charges = [
    ...new Set(
      episodes.map((e) => e.top_charge).filter((c): c is string => c != null)
    ),
  ];
  if (charges.length > 0) {
    stats.push({
      label: "Distinct charges",
      value: String(charges.length),
      detail: charges.length === 1 ? chargeLabel(charges[0]) : `Most common: ${chargeLabel(mostCommon(episodes))}`,
    });
  }

  // 5. Longest stay
  const stays = episodes
    .map((e) => (e.stay_days != null ? Number(e.stay_days) : null))
    .filter((s): s is number => s != null);
  if (stays.length > 0) {
    const longest = Math.max(...stays);
    stats.push({
      label: "Longest stay",
      value: longest > 365 ? `${(longest / 365).toFixed(1)} yrs` : `${longest}d`,
    });
  }

  // 6. Current age estimate
  if (person.approx_birth_year) {
    const age = new Date().getFullYear() - person.approx_birth_year;
    const ageAtFirst =
      new Date(person.first_admission).getFullYear() -
      person.approx_birth_year;
    stats.push({
      label: "Estimated age",
      value: `~${age}`,
      detail: `First admitted at ~${ageAtFirst}`,
    });
  }

  // 7. Years in system
  const yearsInSystem = spanDays / 365;
  if (yearsInSystem >= 1) {
    const rate = episodes.length / yearsInSystem;
    stats.push({
      label: "Admission rate",
      value: `${rate.toFixed(1)}/yr`,
      detail: `${episodes.length} in ${yearsInSystem.toFixed(1)} years`,
    });
  }

  // 8. Last seen
  const lastDischarge = person.last_discharge;
  if (lastDischarge) {
    const daysSince = Math.round(
      (Date.now() - new Date(lastDischarge).getTime()) / 86400000
    );
    stats.push({
      label: "Since last release",
      value:
        daysSince > 365
          ? `${(daysSince / 365).toFixed(1)} yrs`
          : `${daysSince}d`,
      detail: `Released ${lastDischarge.slice(0, 10)}`,
    });
  }

  return stats;
}

function mostCommon(episodes: Episode[]): string {
  const counts: Record<string, number> = {};
  for (const e of episodes) {
    if (e.top_charge) {
      counts[e.top_charge] = (counts[e.top_charge] ?? 0) + 1;
    }
  }
  let best = "";
  let bestN = 0;
  for (const [k, v] of Object.entries(counts)) {
    if (v > bestN) {
      best = k;
      bestN = v;
    }
  }
  return best;
}
