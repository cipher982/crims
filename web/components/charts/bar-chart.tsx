"use client";

import {
  BarChart,
  Bar,
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
  horizontal?: boolean;
}

export function SimpleBarChart({
  data,
  title,
  color = "#06b6d4",
  horizontal = false,
}: Props) {
  if (horizontal) {
    return (
      <div>
        <h3 className="mb-3 text-sm font-semibold tracking-[0.14em] uppercase text-[var(--drose-text-muted)]">
          {title}
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} layout="vertical" margin={{ left: 120 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
            <XAxis type="number" tick={{ fill: "#8e93a4", fontSize: 11 }} axisLine={{ stroke: "rgba(255,255,255,0.08)" }} tickLine={false} />
            <YAxis type="category" dataKey="name" width={110} tick={{ fill: "#c2c5cf", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip
              cursor={{ fill: "rgba(99,102,241,0.08)" }}
              contentStyle={{
                background: "rgba(10,10,18,0.96)",
                border: "1px solid rgba(99,102,241,0.2)",
                borderRadius: 12,
                color: "#fafafa",
                boxShadow: "0 12px 30px rgba(0,0,0,0.35)",
              }}
            />
            <Bar dataKey="value" fill={color} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold tracking-[0.14em] uppercase text-[var(--drose-text-muted)]">
        {title}
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fill: "#8e93a4", fontSize: 11 }} axisLine={{ stroke: "rgba(255,255,255,0.08)" }} tickLine={false} />
          <YAxis tick={{ fill: "#8e93a4", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip
            cursor={{ fill: "rgba(99,102,241,0.08)" }}
            contentStyle={{
              background: "rgba(10,10,18,0.96)",
              border: "1px solid rgba(99,102,241,0.2)",
              borderRadius: 12,
              color: "#fafafa",
              boxShadow: "0 12px 30px rgba(0,0,0,0.35)",
            }}
          />
          <Bar dataKey="value" fill={color} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
