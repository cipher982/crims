"use client";

import { useMemo } from "react";
import { chargeLabel } from "@/lib/format";

interface Episode {
  episode_num: number;
  admit_date: string;
  discharge_date: string | null;
  stay_days: number | null;
  gap_days: number | null;
  top_charge: string | null;
}

/** Duty-cycle timeline: red = in jail, empty = free */
export function JailTimeline({ episodes }: { episodes: Episode[] }) {
  const { segments, startDate, endDate, totalDays, pctIncarcerated } =
    useMemo(() => computeTimeline(episodes), [episodes]);

  if (segments.length === 0) return null;

  const years = getYearMarkers(startDate, endDate);

  return (
    <div className="drose-panel">
      <div className="mb-1 flex items-baseline justify-between">
        <h2 className="drose-panel-title">
          Incarceration Timeline
        </h2>
        <span className="text-sm text-[var(--drose-text-muted)]">
          {fmt(startDate)} — {fmt(endDate)}
        </span>
      </div>
      <p className="mb-4 text-sm text-[var(--drose-text-muted)]">
        {pctIncarcerated.toFixed(1)}% of time incarcerated since first
        admission ({totalDays.toLocaleString()} days tracked)
      </p>

      <div className="relative h-10 w-full overflow-hidden rounded-full border border-white/8 bg-white/6">
        {segments.map((seg, i) => (
          <div
            key={i}
            className="absolute top-0 h-full rounded-sm"
            style={{
              left: `${seg.startPct}%`,
              width: `${Math.max(seg.widthPct, 0.3)}%`,
              background:
                seg.type === "jail"
                  ? "linear-gradient(180deg, #fb7185 0%, #be123c 100%)"
                  : "transparent",
            }}
            title={seg.tooltip}
          />
        ))}
      </div>

      <div className="relative mt-2 h-4 w-full text-[10px] text-[var(--drose-text-muted)]">
        {years.map((y) => (
          <span
            key={y.year}
            className="absolute"
            style={{ left: `${y.pct}%`, transform: "translateX(-50%)" }}
          >
            {y.year}
          </span>
        ))}
      </div>

      <div className="mt-3 flex items-center gap-4 text-xs text-[var(--drose-text-muted)]">
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded-sm bg-rose-400" /> In
          jail
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded-sm border border-white/10 bg-white/6" />{" "}
          Free
        </span>
        <span>
          {episodes.length} episodes — hover for details
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function computeTimeline(episodes: Episode[]) {
  const sorted = [...episodes].sort(
    (a, b) => new Date(a.admit_date).getTime() - new Date(b.admit_date).getTime()
  );

  if (sorted.length === 0)
    return { segments: [], startDate: new Date(), endDate: new Date(), totalDays: 0, pctIncarcerated: 0 };

  const startDate = new Date(sorted[0].admit_date);
  // End date: last discharge, or last admit + stay, or today
  const lastEp = sorted[sorted.length - 1];
  const endDate = lastEp.discharge_date
    ? new Date(lastEp.discharge_date)
    : new Date(
        Math.max(
          new Date(lastEp.admit_date).getTime() + Number(lastEp.stay_days ?? 1) * 86400000,
          Date.now()
        )
      );

  const rawSpanMs = endDate.getTime() - startDate.getTime();
  const totalMs = Math.max(rawSpanMs, 86400000);
  const totalDays = Math.max(1, Math.round(totalMs / 86400000));

  type Seg = { type: "jail" | "free"; startPct: number; widthPct: number; tooltip: string };
  const segments: Seg[] = [];
  let jailDays = 0;

  for (let i = 0; i < sorted.length; i++) {
    const ep = sorted[i];
    const admitMs = new Date(ep.admit_date).getTime() - startDate.getTime();
    const stay = Number(ep.stay_days ?? 1);
    jailDays += stay;

    const startPct = (admitMs / totalMs) * 100;
    const widthPct = ((stay * 86400000) / totalMs) * 100;

    segments.push({
      type: "jail",
      startPct,
      widthPct,
      tooltip: `#${ep.episode_num}: ${fmt(new Date(ep.admit_date))} — ${stay}d — ${chargeLabel(ep.top_charge)}`,
    });
  }

  const pctIncarcerated = totalDays > 0 ? Math.min(100, (jailDays / totalDays) * 100) : 0;

  return { segments, startDate, endDate, totalDays, pctIncarcerated };
}

function getYearMarkers(start: Date, end: Date) {
  const totalMs = Math.max(end.getTime() - start.getTime(), 86400000);
  const markers: { year: number; pct: number }[] = [];
  const startYear = start.getFullYear();
  const endYear = end.getFullYear();
  for (let y = startYear; y <= endYear; y++) {
    const jan1 = new Date(y, 0, 1).getTime();
    const pct = ((jan1 - start.getTime()) / totalMs) * 100;
    if (pct >= 0 && pct <= 100) {
      markers.push({ year: y, pct });
    }
  }
  return markers;
}

function fmt(d: Date) {
  return d.toISOString().slice(0, 10);
}
