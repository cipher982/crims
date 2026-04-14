import fs from "fs/promises";
import path from "path";
import { getDataDir } from "./db";

export interface SourceRow {
  source: string;
  agency: string;
  dataset: string;
  coverage: string;
  grain: string;
  key: string;
  role: string;
}

export interface DerivedDatasetRow {
  name: string;
  grain: string;
  builtBy: string;
  method: string;
  confidence: "exact" | "candidate" | "mixed" | "unsupported";
  usedFor: string;
}

export interface JoinRow {
  join: string;
  fields: string;
  status: "exact" | "candidate" | "unsupported";
  supports: string;
  caveat: string;
}

export interface BuildStep {
  script: string;
  outputs: string;
  purpose: string;
}

export const CURRENT_APP_SOURCES: SourceRow[] = [
  {
    source: "NYC DOC Inmate Admissions",
    agency: "NYC Department of Correction",
    dataset: "6teu-xtgp",
    coverage: "2014-2026",
    grain: "Jail admission event",
    key: "INMATEID + ADMITTED_DT",
    role: "Primary source for exact DOC episode histories and person rollups.",
  },
  {
    source: "NYC DOC Inmate Discharges",
    agency: "NYC Department of Correction",
    dataset: "94ri-3ium",
    coverage: "2014-2026",
    grain: "Jail discharge event",
    key: "INMATEID + ADMITTED_DT",
    role: "Supplies discharge dates and age-at-discharge for stay lengths and birth-year imputation.",
  },
  {
    source: "NYPD Arrests Historic",
    agency: "New York City Police Department",
    dataset: "8h9b-rp9u",
    coverage: "2006-2024",
    grain: "Arrest event",
    key: "ARREST_KEY",
    role: "Feeds the arrest-to-DOC bridge after penal-code parsing and demographic/date filtering.",
  },
];

export const REPO_PANEL_SOURCES: SourceRow[] = [
  ...CURRENT_APP_SOURCES,
  {
    source: "NYPD Complaints Historic",
    agency: "New York City Police Department",
    dataset: "qgea-i56i",
    coverage: "2006-2024",
    grain: "Complaint event",
    key: "cmplnt_num",
    role: "Used in the broader public event panel and arrest-to-complaint candidate matching.",
  },
  {
    source: "NYPD Summonses Historic",
    agency: "New York City Police Department",
    dataset: "sv2w-rv3k",
    coverage: "2006-2024",
    grain: "Summons event",
    key: "SUMMONS_KEY",
    role: "Included as a standalone event source in the broader public event panel.",
  },
  {
    source: "Census Batch Geocoder",
    agency: "U.S. Census Bureau",
    dataset: "coordinatesbatch endpoint",
    coverage: "Current geography benchmark",
    grain: "Coordinate-to-geography lookup",
    key: "Longitude + Latitude",
    role: "Adds tract and block-group geography to NYPD event rows with coordinates.",
  },
];

export const DOCUMENTED_NOT_YET_SURFACED: SourceRow[] = [
  {
    source: "OCA-STAT Act extract",
    agency: "UCS / OCA",
    dataset: "Bulk CSV",
    coverage: "2021-2025 arraignments",
    grain: "De-identified case",
    key: "No public person key",
    role: "Documented in repo inventory, but not wired into the current explorer.",
  },
  {
    source: "OCA Pretrial Release extract",
    agency: "UCS / OCA + DCJS",
    dataset: "Bulk CSV",
    coverage: "2020-2024 arraignments",
    grain: "De-identified case",
    key: "arr_cycle_id within same arrest",
    role: "Useful for court detail, but not person-linkable across arrests in public form.",
  },
  {
    source: "DCJS Supplemental Pretrial",
    agency: "DCJS",
    dataset: "Bulk ZIP / CSV",
    coverage: "2019-2024 arraignments",
    grain: "De-identified case",
    key: "caseid",
    role: "Documented in the repo, but not part of the current web app pipeline.",
  },
  {
    source: "DOCCS aggregate tables",
    agency: "New York State DOCCS",
    dataset: "Open Data NY",
    coverage: "2008+",
    grain: "Aggregate",
    key: "County + year",
    role: "Validation/context only. No prison person identifier is public.",
  },
];

export const CURRENT_APP_DATASETS: DerivedDatasetRow[] = [
  {
    name: "doc_recidivism_persons.parquet",
    grain: "One row per DOC person",
    builtBy: "scripts/analyze_doc_recidivism.py",
    method:
      "Join DOC admissions to discharges on INMATEID + admit_date, sequence episodes, then aggregate to person-level metrics.",
    confidence: "exact",
    usedFor: "Homepage leader table, search results, person summary cards, and tiering.",
  },
  {
    name: "doc_recidivism_episodes.parquet",
    grain: "One row per DOC admission episode",
    builtBy: "scripts/analyze_doc_recidivism.py",
    method:
      "Exact DOC episode history with discharge date, stay_days, gap_days, episode order, and imputed birth year.",
    confidence: "exact",
    usedFor: "Person timelines, episode charts, stay/gap statistics, and raw episode history.",
  },
  {
    name: "doc_cohort_recidivism.parquet",
    grain: "One row per person-cohort outcome",
    builtBy: "scripts/analyze_doc_cohort_recidivism.py",
    method:
      "Build release cohorts from DOC episodes and mark whether each person returned within 1, 2, or 3 years when follow-up is observable.",
    confidence: "exact",
    usedFor: "Homepage 1-year return-rate trend and cohort-based recidivism framing.",
  },
  {
    name: "arrest_doc_bridge.parquet",
    grain: "One row per candidate arrest-to-admission pair",
    builtBy: "scripts/build_arrest_doc_bridge.py",
    method:
      "Match arrests to DOC admissions on same date, normalized sex, parsed penal code, and compatible age bucket, then keep only unique 1:1 pairs.",
    confidence: "candidate",
    usedFor: "Person arrest tables, arrest map points, and bridge subset counts.",
  },
];

export const BROADER_REPO_DATASETS: DerivedDatasetRow[] = [
  {
    name: "nypd_arrests_<year>_research_dataset.parquet",
    grain: "One row per arrest with complaint-match status",
    builtBy: "scripts/build_arrest_research_dataset_polars.py",
    method:
      "Filter arrests by year, join to year-specific complaint subset on date + precinct + offense code + borough, then tighten with demographics.",
    confidence: "candidate",
    usedFor: "Broader public event graph work outside the current web routes.",
  },
  {
    name: "public_event_spine_<year>_census_geo.parquet",
    grain: "One row per public event",
    builtBy:
      "scripts/build_public_event_spine_polars.py + scripts/build_public_event_spine_census_geo.py",
    method:
      "Stack yearly arrests, complaints, summonses, DOC admissions, and DOC discharges into one schema, then geocode unique coordinates with a cache.",
    confidence: "mixed",
    usedFor: "Broader panel analysis and cross-source coverage profiling.",
  },
  {
    name: "public_event_panel_<start>_<end>_census_geo.parquet",
    grain: "Multi-year stacked event panel",
    builtBy: "scripts/build_public_event_panel.py",
    method:
      "Concatenate yearly geocoded event spines into a longitudinal public event panel.",
    confidence: "mixed",
    usedFor: "Repo-level inventory and cross-source coverage analysis.",
  },
];

export const JOIN_ROWS: JoinRow[] = [
  {
    join: "DOC admissions ↔ DOC discharges",
    fields: "INMATEID + admit_date",
    status: "exact",
    supports: "Stay lengths, gap lengths, ordered jail episodes, and DOC person histories.",
    caveat: "Exact within the public DOC feeds, but only for the jail stage.",
  },
  {
    join: "DOC episodes ↔ DOC person summaries",
    fields: "Aggregation over INMATEID",
    status: "exact",
    supports: "Repeat-admission counts, tiers, charge-change counts, and person profiles.",
    caveat: "Still a DOC-only identity, not a citywide criminal-justice person key.",
  },
  {
    join: "NYPD arrests ↔ DOC admissions",
    fields: "date + sex + parsed penal code + imputed age bucket",
    status: "candidate",
    supports: "A narrow arrest-to-jail bridge subset for mapped/contextual arrest detail.",
    caveat: "Not ground truth. Only unique 1:1 matches are kept to favor precision over coverage.",
  },
  {
    join: "NYPD arrests ↔ NYPD complaints",
    fields: "date + precinct + offense code + borough + demographics",
    status: "candidate",
    supports: "Broader repo event-graph analysis outside the current web explorer.",
    caveat: "Ambiguous and incomplete, especially in earlier years.",
  },
  {
    join: "Anything ↔ public court bulk data",
    fields: "None",
    status: "unsupported",
    supports: "No public person-level court linkage in this app.",
    caveat: "The court extracts documented in the repo are intentionally de-identified.",
  },
  {
    join: "Anything ↔ state prison person records",
    fields: "None",
    status: "unsupported",
    supports: "No person-level prison linkage in this app.",
    caveat: "Public DOCCS releases are aggregate only.",
  },
];

export const BUILD_STEPS: BuildStep[] = [
  {
    script: "scripts/download_public_data.py",
    outputs: "Raw CSVs under data/raw/",
    purpose:
      "Pull the core NYC open-data inputs used across the repo, including arrests, complaints, summonses, and DOC feeds.",
  },
  {
    script: "scripts/analyze_doc_recidivism.py",
    outputs:
      "doc_recidivism_persons.parquet, doc_recidivism_episodes.parquet, doc_recidivism_summary.json",
    purpose:
      "Construct exact jail episode histories and person-level repeat-admission summaries from DOC admissions/discharges.",
  },
  {
    script: "scripts/analyze_doc_cohort_recidivism.py",
    outputs:
      "doc_cohort_recidivism.parquet, doc_cohort_recidivism_summary.json",
    purpose:
      "Create cohort-based 1/2/3-year return outcomes with censoring based on observed follow-up windows.",
  },
  {
    script: "scripts/build_arrest_doc_bridge.py",
    outputs:
      "arrest_doc_bridge.parquet, arrest_doc_bridge_episodes.parquet, arrest_doc_bridge_summary.json",
    purpose:
      "Build the candidate arrest-to-jail bridge and keep only unique 1:1 matches.",
  },
  {
    script: "scripts/build_arrest_research_dataset_polars.py",
    outputs: "nypd_arrests_<year>_research_dataset.parquet",
    purpose:
      "Annotate yearly arrests with complaint-match quality for the broader event-graph work.",
  },
  {
    script: "scripts/build_public_event_spine_polars.py",
    outputs: "public_event_spine_<year>.parquet",
    purpose:
      "Standardize arrests, complaints, summonses, and DOC events into one event schema.",
  },
  {
    script: "scripts/build_public_event_spine_census_geo.py",
    outputs: "public_event_spine_<year>_census_geo.parquet",
    purpose:
      "Geocode unique coordinates with the Census batch geocoder and cache the results.",
  },
  {
    script: "scripts/build_public_event_panel.py",
    outputs: "public_event_panel_<start>_<end>_census_geo.parquet",
    purpose:
      "Concatenate yearly event spines into the multi-year public event panel.",
  },
];

export const NON_CLAIMS = [
  "A DOC person page is an exact jail-stage history keyed by INMATEID, not a citywide criminal-justice identity.",
  "The arrest-to-DOC bridge is a candidate subset designed for precision, not a full arrest coverage layer.",
  "Court outcomes are not linked in the current web app because the public court extracts do not expose a cross-case public person key.",
  "State prison, parole, and statewide multi-arrest recidivism remain unsupported in public bulk data.",
  "DOC race and charge fields are not strong enough to support broad cross-system identity claims on their own.",
];

interface PanelProfile {
  total_rows: number;
  source_counts?: Array<{ EVENT_SOURCE: string; rows: number }>;
}

export async function getOptionalPanelProfile(): Promise<PanelProfile | null> {
  return readOptionalJson<PanelProfile>(
    path.join(getMetaDir(), "public_event_panel_2014_2024_census_geo_profile.json")
  );
}

function getMetaDir(): string {
  return path.join(getDataDir(), "..", "meta");
}

async function readOptionalJson<T>(filePath: string): Promise<T | null> {
  try {
    const raw = await fs.readFile(filePath, "utf8");
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}
