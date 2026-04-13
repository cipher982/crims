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
  color = "#3b82f6",
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
      <h3 className="mb-2 text-sm font-medium text-gray-700">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={fmt} />
          <Tooltip formatter={(value) => formatTooltipValue(value)} />
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
