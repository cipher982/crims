"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import type { SearchFilters } from "@/lib/types";

interface Props {
  options: {
    tiers: string[];
    races: string[];
    sexes: string[];
  };
  current: SearchFilters;
}

function buildSearchUrl(
  searchParamsString: string,
  updates: Record<string, string>
): string {
  const params = new URLSearchParams(searchParamsString);
  for (const [key, rawValue] of Object.entries(updates)) {
    const value = rawValue.trim();
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
  }
  return params.toString() ? `/search?${params.toString()}` : "/search";
}

export function SearchFilterForm({ options, current }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchParamsString = searchParams.toString();
  const [isPending, startTransition] = useTransition();
  const [draftMinAdmissions, setDraftMinAdmissions] = useState(
    current.minAdmissions?.toString() ?? ""
  );
  const [draftCharge, setDraftCharge] = useState(current.charge ?? "");

  function replaceUrl(updates: Record<string, string>) {
    const url = buildSearchUrl(searchParamsString, updates);
    startTransition(() => {
      router.replace(url, { scroll: false });
    });
  }

  useEffect(() => {
    const nextCharge = draftCharge.trim();
    const nextMin = draftMinAdmissions.trim();
    const currentCharge = current.charge ?? "";
    const currentMin = current.minAdmissions?.toString() ?? "";
    if (nextCharge === currentCharge && nextMin === currentMin) {
      return;
    }

    const timeout = window.setTimeout(() => {
      const url = buildSearchUrl(searchParamsString, {
        charge: nextCharge,
        min: nextMin,
      });
      startTransition(() => {
        router.replace(url, { scroll: false });
      });
    }, 300);

    return () => window.clearTimeout(timeout);
  }, [
    current.charge,
    current.minAdmissions,
    draftCharge,
    draftMinAdmissions,
    router,
    searchParamsString,
    startTransition,
  ]);

  function update(key: string, value: string) {
    replaceUrl({ [key]: value });
  }

  const hasActiveFilters =
    Boolean(current.tier) ||
    Boolean(current.race) ||
    Boolean(current.sex) ||
    Boolean(current.minAdmissions) ||
    Boolean(current.charge) ||
    current.sort !== "total_admissions" ||
    current.dir !== "desc";

  return (
    <div className="drose-panel drose-form-panel">
      <div className="drose-form-toolbar">
        <p className="drose-form-toolbar-copy">
          Filters live in the URL so views stay shareable and restorable. Text
          inputs update after a short pause.
        </p>
        <div className="drose-form-toolbar-meta">
          {hasActiveFilters && (
            <Link
              href="/search"
              className="drose-subtle-link"
            >
              Clear filters
            </Link>
          )}
          <span className={`drose-status ${isPending ? "drose-status-pending" : ""}`}>
            {isPending ? "Updating..." : "Ready"}
          </span>
        </div>
      </div>

      <div className="drose-control-grid">
        <select
          className="drose-control"
          value={current.tier ?? ""}
          onChange={(e) => update("tier", e.target.value)}
        >
          <option value="">All Tiers</option>
          {options.tiers.map((t) => (
            <option key={t} value={t}>
              {t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </option>
          ))}
        </select>

        <select
          className="drose-control"
          value={current.race ?? ""}
          onChange={(e) => update("race", e.target.value)}
        >
          <option value="">All Races</option>
          {options.races.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>

        <select
          className="drose-control"
          value={current.sex ?? ""}
          onChange={(e) => update("sex", e.target.value)}
        >
          <option value="">All Sexes</option>
          {options.sexes.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <input
          type="number"
          className="drose-control w-28"
          placeholder="Min admits"
          value={draftMinAdmissions}
          onChange={(e) => setDraftMinAdmissions(e.target.value)}
          min={1}
        />

        <input
          type="search"
          className="drose-control w-44"
          placeholder="Charge code"
          value={draftCharge}
          onChange={(e) => setDraftCharge(e.target.value)}
        />

        <select
          className="drose-control"
          value={current.sort ?? "total_admissions"}
          onChange={(e) => update("sort", e.target.value)}
        >
          <option value="total_admissions">Sort: Admissions</option>
          <option value="first_admission">Sort: First Admission</option>
          <option value="last_admission">Sort: Last Admission</option>
          <option value="avg_stay_days">Sort: Avg Stay</option>
          <option value="distinct_charges">Sort: Distinct Charges</option>
        </select>

        <select
          className="drose-control"
          value={current.dir ?? "desc"}
          onChange={(e) => update("dir", e.target.value)}
        >
          <option value="desc">Descending</option>
          <option value="asc">Ascending</option>
        </select>
      </div>
    </div>
  );
}
