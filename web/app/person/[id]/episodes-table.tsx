"use client";

import { useState } from "react";
import type { Episode } from "@/lib/types";
import { chargeLabel, formatDate } from "@/lib/format";

type SortKey = "episode_num" | "admit_date" | "stay_days" | "gap_days" | "top_charge";

export function EpisodesTable({ episodes }: { episodes: Episode[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("episode_num");
  const [sortAsc, setSortAsc] = useState(true);

  const sorted = [...episodes].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return sortAsc ? cmp : -cmp;
  });

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  function header(label: string, key: SortKey) {
    return (
      <th
        className="cursor-pointer select-none hover:text-[var(--drose-text-secondary)]"
        onClick={() => toggleSort(key)}
      >
        {label}
        {sortKey === key && (
          <span className="ml-1">{sortAsc ? "▲" : "▼"}</span>
        )}
      </th>
    );
  }

  return (
    <div className="drose-table-wrap">
      <table className="drose-table">
        <thead>
          <tr>
            {header("#", "episode_num")}
            {header("Admitted", "admit_date")}
            <th>Discharged</th>
            {header("Stay (days)", "stay_days")}
            {header("Gap (days)", "gap_days")}
            {header("Charge", "top_charge")}
            <th>Status</th>
            <th>Age</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((e) => (
            <tr key={e.episode_num}>
              <td className="drose-mono text-[var(--drose-text-muted)]">{e.episode_num}</td>
              <td className="drose-mono">{formatDate(e.admit_date)}</td>
              <td className="drose-mono">{formatDate(e.discharge_date)}</td>
              <td>{e.stay_days ?? "—"}</td>
              <td>{e.gap_days ?? "—"}</td>
              <td>{chargeLabel(e.top_charge)}</td>
              <td>{e.status_code ?? "—"}</td>
              <td>{e.age_at_discharge ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
