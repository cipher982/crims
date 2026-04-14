"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  ReferenceLine,
} from "recharts";
import { chargeLabel } from "@/lib/format";

interface Props {
  episodes: {
    episode_num: number;
    admit_date: string;
    stay_days: number | null;
    gap_days: number | null;
    top_charge: string | null;
  }[];
  avgStay: number | null;
}

export function EpisodeChart({ episodes, avgStay }: Props) {
  if (episodes.length < 2) return null;

  const data = episodes.map((e) => ({
    name: `#${e.episode_num}`,
    stay: Number(e.stay_days ?? 0),
    gap: e.gap_days != null ? Number(e.gap_days) : 0,
    charge: e.top_charge,
    date: e.admit_date?.slice(0, 10),
  }));

  // Compute stay trend
  const stays = data.map((d) => d.stay);
  const firstHalf = stays.slice(0, Math.floor(stays.length / 2));
  const secondHalf = stays.slice(Math.floor(stays.length / 2));
  const avgFirst =
    firstHalf.reduce((s, v) => s + v, 0) / (firstHalf.length || 1);
  const avgSecond =
    secondHalf.reduce((s, v) => s + v, 0) / (secondHalf.length || 1);

  const trend =
    avgSecond > avgFirst * 1.5
      ? "Stays are getting longer"
      : avgSecond < avgFirst * 0.6
        ? "Stays are getting shorter"
        : "Stay length is stable";
  const trendColor =
    avgSecond > avgFirst * 1.5
      ? "text-rose-300"
      : avgSecond < avgFirst * 0.6
        ? "text-emerald-300"
        : "text-[var(--drose-text-muted)]";

  return (
    <div className="drose-panel">
      <div className="mb-1 flex items-baseline justify-between">
        <h2 className="drose-panel-title">
          Episode Breakdown
        </h2>
        <span className={`text-sm font-medium ${trendColor}`}>{trend}</span>
      </div>
      <p className="mb-4 text-sm text-[var(--drose-text-muted)]">
        Each episode: red = days in jail, gray = days free before next arrest
      </p>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 10, fill: "#8e93a4" }}
            axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
            tickLine={false}
            interval={data.length > 30 ? Math.floor(data.length / 15) : 0}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#8e93a4" }}
            axisLine={false}
            tickLine={false}
            label={{ value: "days", angle: -90, position: "insideLeft", fontSize: 11, fill: "#8e93a4" }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0]?.payload;
              return (
                <div className="rounded-xl border border-[rgba(99,102,241,0.2)] bg-[rgba(10,10,18,0.96)] px-3 py-2 text-xs shadow-lg shadow-black/40">
                  <div className="font-semibold text-white">
                    Episode {d.name} — {d.date}
                  </div>
                  <div className="text-rose-300">{d.stay}d in jail</div>
                  {d.gap > 0 && (
                    <div className="text-[var(--drose-text-muted)]">{d.gap}d free after</div>
                  )}
                  {d.charge && (
                    <div className="text-[var(--drose-text-secondary)]">
                      {chargeLabel(d.charge)}
                    </div>
                  )}
                </div>
              );
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 12, color: "#c2c5cf" }}
            formatter={(value: string) =>
              value === "stay" ? "In jail" : "Free after"
            }
          />
          <Bar
            dataKey="stay"
            stackId="a"
            fill="#fb7185"
            radius={[0, 0, 0, 0]}
            name="stay"
          />
          <Bar
            dataKey="gap"
            stackId="a"
            fill="rgba(255,255,255,0.18)"
            radius={[3, 3, 0, 0]}
            name="gap"
          />
          {avgStay && (
            <ReferenceLine
              y={Math.round(avgStay)}
              stroke="#fb7185"
              strokeDasharray="4 4"
              label={{
                value: `avg stay ${Math.round(avgStay)}d`,
                fontSize: 10,
                fill: "#fb7185",
                position: "right",
              }}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
