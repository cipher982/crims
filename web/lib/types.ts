export interface Person {
  INMATEID: string;
  total_admissions: number;
  first_admission: string;
  last_admission: string;
  last_discharge: string | null;
  avg_stay_days: number | null;
  median_stay_days: number | null;
  avg_gap_days: number | null;
  median_gap_days: number | null;
  race: string | null;
  sex: string | null;
  approx_birth_year: number | null;
  first_known_charge: string | null;
  last_known_charge: string | null;
  distinct_charges: number;
  recidivism_tier: string;
}

export interface Episode {
  INMATEID: string;
  admit_date: string;
  discharge_date: string | null;
  race: string | null;
  sex: string | null;
  status_code: string | null;
  top_charge: string | null;
  age_at_discharge: number | null;
  stay_days: number | null;
  gap_days: number | null;
  episode_num: number;
  total_episodes: number;
  approx_birth_year: number | null;
}

export interface CohortRow {
  cohort_year: number;
  returned_1yr: boolean | null;
  returned_2yr: boolean | null;
  returned_3yr: boolean | null;
  charge_category: string | null;
  age_group: string | null;
  race: string | null;
  sex: string | null;
}

export interface BridgeRow {
  ARREST_KEY: string;
  arrest_date: string;
  penal_code: string;
  law_category: string | null;
  arrest_sex: string | null;
  arrest_age_group: string | null;
  arrest_race: string | null;
  arrest_boro: string | null;
  arrest_precinct: number | null;
  lat: number | null;
  lon: number | null;
  INMATEID: string;
}

export interface SearchFilters {
  tier?: string;
  race?: string;
  sex?: string;
  minAdmissions?: number;
  charge?: string;
  sort?: string;
  dir?: "asc" | "desc";
}
