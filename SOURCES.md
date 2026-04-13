# Data Sources

## Public Bulk Sources (in panel)

| Source | Slug / System | Grain | Best Key | Coverage | Demographics | Joinability |
|--------|--------------|-------|----------|----------|-------------|-------------|
| NYPD Arrests | `8h9b-rp9u` | arrest event | `arrest_key` | 2006-2024 | sex, race, age bucket (all 100%) | Strong within table; heuristic to complaints |
| NYPD Complaints | `qgea-i56i` | complaint event | `cmplnt_num` | 2006-2024 | sex, race, age bucket (standard buckets; raw integer ages are <0.01%) | Context table; weak to arrests |
| NYPD Summonses | `sv2w-rv3k` | summons event | `summons_key` | 2006-2024 | sex 94%, race 74%, age 98% | Standalone; no cross-stage links |
| DOC Admissions | `6teu-xtgp` | jail admission | `inmateid` | 2014-2026 | sex 100%, race 100% (3 values only), no age, no boro. `TOP_CHARGE` 38% non-null (penal law format e.g. `155.25`) | Strong to DOC discharges via `inmateid`; candidate bridge to arrests via date+sex+charge+imputed age |
| DOC Discharges | `94ri-3ium` | jail discharge | `inmateid` | 2014-2026 | sex 100%, race 100%, `AGE` 100% (integer at discharge) | Strong to DOC admissions. Discharge `AGE` enables birth year imputation for all DOC people. |
| DOC Daily Custody | `7479-ugqb` | daily snapshot | `inmateid` | current | sex, race, age, custody level | Enrichable from episode joins |

YTD feeds (`uip8-fykc`, `5uac-w243`, `mv4k-y93f`) exist but have historically lagged by a year. Validate before relying on them.

## Public Bulk Sources (not yet ingested)

| Source | System | Grain | Key | Coverage | Access | Notes |
|--------|--------|-------|-----|----------|--------|-------|
| OCA-STAT Act | UCS/OCA | de-identified case | non-identifiable defendant-docket | 2021-2025 arraignments | Bulk CSV from [ww2.nycourts.gov](https://ww2.nycourts.gov/oca-stat-act-31371) | 28 cols. Disposition type, sentence, demographics, arresting agency (NYPD precinct codes). Month-only dates. **Downloaded.** |
| OCA Pretrial Release | UCS/OCA + DCJS | de-identified case | `arr_cycle_id` (links dockets from same arrest), `Internal_Case_ID` | 2020-2024 arraignments | Bulk CSV from [ww2.nycourts.gov](https://ww2.nycourts.gov/pretrial-release-data-33136) | **130 cols.** Judge names, bail detail, criminal history (prior VFO/felony/misd counts from DCJS CCH), rearrest tracking (18.2% rearrested — real person-level via NYSID), custody days, sentence detail. `arr_cycle_id` 83% coverage, links dockets within same arrest only. Month-only dates except disposition. Statewide (54% NYC). **Downloaded.** |
| DCJS Supplemental Pretrial | DCJS | arrest-to-disposition case | `caseid` (de-identified per-case) | 2019-2024 arraignments | ZIP from [criminaljustice.ny.gov](https://criminaljustice.ny.gov/crimnet/ojsa/stats.htm) | **1.38M rows, 114 cols.** DCJS-linked arrest→disposition. 8 rearrest indicators (VFO/nonVFO/misd/firearm × full/180-day), prior criminal history, `arr_agency_name` has NYPD precinct codes (420K NYC rows). Month-only dates. No person ID across cases. **Downloaded.** |
| Detained Pretrial | UCS/OCA | monthly detained snapshot | de-identified | Jan 2024-Feb 2025 | Bulk CSV from [ww2.nycourts.gov](https://ww2.nycourts.gov/detained-pretrial-36781) | 106K rows. Rikers pretrial detainees, monthly snapshot. No person ID, binary charge flags only. **Downloaded.** |
| DOCCS Prison Admissions | Open Data NY | aggregate | county + year | 2008+ | Bulk CSV from data.ny.gov | Aggregate only — no DIN, no NYSID. Validation/context use. |
| DOCCS Recidivism | Open Data NY | aggregate | county + year | 2008+ | Bulk CSV from data.ny.gov | Aggregate recidivism rates. Not person-level. |
| NYS Adult Arrests by County | `rikd-mt35` | county-year aggregate | county + year | 1970-2025 | Bulk | Aggregate validation only. |
| Shooting Offenders | `gdk4-mbsv` | suspect-offender event | `perp_id` | 2006+ | Bulk | Violent subset; not a general join table. |

## Lookup Systems (not bulk, not scriptable)

| System | What | Person ID? | Usable for research? |
|--------|------|-----------|---------------------|
| CHRS (OCA) | Court conviction/pending search | Name + DOB query | No — fee-based, per-search, no API |
| WebCrims | Live criminal court case lookup | Case number / name | No — anti-bot ToS, no API, no bulk |
| NYC DOC Person In Custody | Current/historical custody | NYSID or Book & Case or name | No — portal restrictions |
| DOCCS Incarcerated Lookup | Prison/parole status | DIN or name + YOB | No — interactive only, NYSID hidden |

## Restricted Identifiers (not in public data)

These exist inside agency systems and enable end-to-end person tracking. Accessing them requires a DCJS research data agreement or equivalent.

| Identifier | Scope | Maintained by | Links |
|------------|-------|--------------|-------|
| **NYSID** | Statewide person (fingerprint-based) | DCJS | Arrest ↔ court ↔ jail ↔ prison ↔ parole |
| **CJTN** | Arrest-to-court transaction | DCJS | One arrest event to its arraignment/case |
| **Court docket #** | Court case | OCA/UCS | Case processing within courts |
| **DIN** | State prison person | DOCCS | Prison custody/release/parole |
| **Book & Case** | NYC jail custody reference | NYC DOC | Jail episodes |

DCJS is the statewide hub. NYSID + CJTN are the core shared keys between agencies. OCA passes court dispositions to DCJS using these. NYC DOC notably does **not** record CJTN or arrest dates — even Vera Institute had to match DOC to arrests by date logic in their restricted-data research.

## Cross-Source Join Surfaces

| Join | Fields | Quality | Notes |
|------|--------|---------|-------|
| DOC admissions ↔ discharges | `INMATEID` + `ADMITTED_DT` | Exact, 97.7% | Strong |
| Arrests ↔ complaints | date + precinct + offense code + borough + demographics | Heuristic, ~40% unique | Worse in 2014-2017 |
| Arrests ↔ DOC admissions | date + sex + penal code + imputed age group | Heuristic, ~10% unique | `LAW_CODE` → penal code mapping: `PL XXXYYZZZ` → `XXX.YY`. Birth year from discharge `AGE`. DOC race is useless (3 values, 43% UNKNOWN). |
| Anything ↔ OCA court data | None | Impossible | OCA extracts are intentionally de-identified |
| Anything ↔ DOCCS prison | None | Impossible | Only aggregates published |

## Access Paths for Restricted Data

- **DCJS research agreement**: DCJS can issue anonymized research IDs under data use agreements + IRB. This is how Vera, MOCJ, and academic researchers get linked person-level data.
- **FOIL**: Not the right mechanism for court records (governed by Judiciary Law 255, not FOIL). FOIL to NYC DOC via OpenRecords may yield data dictionaries or historical extracts.
- **OCA/UCS UCE (Universal Criminal Extract)**: Daily incremental bulk SFTP feed of court docket data. Application form exists: [cognitoforms.com/NYSUnifiedCourtSystem/BulkDataApplication](https://www.cognitoforms.com/NYSUnifiedCourtSystemOCADivisionOfTechnology/BulkDataApplication). Described as "select agencies" but form is open. Worth applying — worst case is rejection. FAQ: [portal.nycourts.gov/UCE/UCE_FAQ/](https://portal.nycourts.gov/UCE/UCE_FAQ/)
