import { CHARGE_LABELS } from "./constants";

export function chargeLabel(code: string | null | undefined): string {
  if (!code) return "Unknown";
  const label = CHARGE_LABELS[code];
  return label ? `${code} (${label})` : code;
}

export function formatDate(d: string | null | undefined): string {
  if (!d) return "—";
  // DuckDB returns dates as "YYYY-MM-DD" strings
  return d.slice(0, 10);
}

export function formatNumber(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString();
}

export function tierLabel(tier: string): string {
  return tier
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
