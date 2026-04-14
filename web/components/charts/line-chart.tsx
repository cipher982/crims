"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface Props {
  data: { name: string; value: number }[];
  title: string;
  color?: string;
  /** If set, formats Y values as percentage */
  pct?: boolean;
}

export function SimpleLineChart({
  data,
  title,
  color = "#ec4899",
  pct = false,
}: Props) {
  const fmt = pct ? (v: number) => `${(v * 100).toFixed(0)}%` : undefined;

  function formatTooltipValue(value: unknown) {
    if (value == null) return "—";
    const numericValue =
      typeof value === "number" ? value : Number.parseFloat(String(value));
    if (!Number.isFinite(numericValue)) {
      return String(value);
    }
    return fmt ? fmt(numericValue) : numericValue;
  }

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold tracking-[0.14em] uppercase text-[var(--drose-text-muted)]">
        {title}
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            tick={{ fill: "#8e93a4", fontSize: 11 }}
            axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={fmt}
            tick={{ fill: "#8e93a4", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value) => formatTooltipValue(value)}
            contentStyle={{
              background: "rgba(10,10,18,0.96)",
              border: "1px solid rgba(99,102,241,0.2)",
              borderRadius: 12,
              color: "#fafafa",
              boxShadow: "0 12px 30px rgba(0,0,0,0.35)",
            }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={{ r: 3, fill: color, stroke: "#030305", strokeWidth: 2 }}
            activeDot={{ r: 5, fill: color, stroke: "#fafafa", strokeWidth: 1 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
