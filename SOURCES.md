# Public Sources

This is the working source sheet. It is deliberately short and only includes sources that matter for the first MVPs.

| Source | Dataset / System | Public | Grain | Best Exposed Key | Coverage Seen | Name / DOB | Joinability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NYPD Arrests | `8h9b-rp9u` | Yes | arrest event | `arrest_key` | 2006-01-01 to 2024-12-31 | No | Strong within table, weak across stages |
| NYPD Arrests YTD | `uip8-fykc` | Yes | arrest event | `arrest_key` | currently appears to stop at 2025, not 2026 | No | Same as above, but feed looks stale |
| NYPD Complaints | `qgea-i56i` | Yes | complaint event | `cmplnt_num` | mostly 2006+ but includes bad legacy dates | No | Useful context table, weak direct joins to arrest |
| NYPD Complaints Current | `5uac-w243` | Yes | complaint event | `cmplnt_num` | currently appears to stop at 2025 | No | Same as above, but feed looks stale |
| NYPD Criminal Summons | `sv2w-rv3k` | Yes | summons event | `summons_key` | 2006-01-01 to 2024-12-31 | No | Useful enforcement table, weak cross-stage joins |
| NYPD Criminal Summons YTD | `mv4k-y93f` | Yes | summons event | `summons_key` | currently appears to stop at 2025 | No | Same as above, but feed looks stale |
| Shooting Offenders | `gdk4-mbsv` | Yes | suspect-offender event | `perp_id` | 2006-present | No | Useful violent subset, not a general arrest join table |
| DOC Inmate Admissions | `6teu-xtgp` | Yes | jail admission | `inmateid` | 2014-01-01 to 2026-03-31 | No | Strong with DOC discharges |
| DOC Inmate Discharges | `94ri-3ium` | Yes | jail discharge | `inmateid` | 2014-01-01 to 2026-03-31 | No | Strong with DOC admissions |
| DOC Daily Inmates In Custody | `7479-ugqb` | Yes | daily custody snapshot | `inmateid` | current daily snapshots | No | Good custody-state table, no names |
| NYS Adult Arrests by County | `rikd-mt35` | Yes | county-year aggregate | county + year | 1970-2025 | No | Aggregate validation only |
| MTA Summonses and Arrests | `7tfn-twae` | Yes | month-agency-force-metric aggregate | month + metric + agency + force | 2019-present | No | Aggregate only |
| CHRS | court lookup | Yes | individual search result | exact name + DOB search | public lookup | Yes, query-side | Manual only, not realistic for bulk |
| WebCrims / WebCriminal | court lookup | Yes | live court case lookup | case number / defendant name | public lookup | sometimes | Public but anti-bot and not a bulk feed |
| NYC Person In Custody Lookup | DOC portal | Yes | current / historical custody lookup | NYSID or Book & Case Number, or name search | historical to Sep 2005 | Yes, portal-side | Public portal, but usage restrictions make it bad for ingestion |
| DOCCS Lookup | prison / parole lookup | Yes | prison / parole status lookup | DIN or name + year of birth | current + some formerly incarcerated people | Yes, portal-side | Useful for spot checks, not a dataset backbone |

## Main Takeaways

- Public bulk data gives us event records, not a public named suspect file.
- The only strong exact public join we have right now is inside DOC via `inmateid`.
- Cross-stage public joins will be heuristic unless we later obtain restricted identifiers.
- The current/YTD NYC feeds need validation each time because the live endpoints we tested looked one year behind.
- For working joins, a targeted complaint slice can be more useful than immediately pulling the full complaint archive.
