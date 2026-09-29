# Data Sources (v1.0, 2026-09-28; D-065)

Where each kind of data can come from, what we use it for, and its trust level. Primary = written into the
lake as a first-class dataset; verification = read to cross-check, never the source of record; candidate =
documented, not integrated.

## 1. In use
| Source | Access | Role | Coverage we use | Caveats |
|---|---|---|---|---|
| **Tushare Pro** | HTTP JSON, token, points tier | primary | prices, fundamentals, reference, options, futures, funds, macro, analysts/events (tier) | per-endpoint permissions; a few double-listings (DATA_CATALOG §3b); no bid/ask |
| **FRED** (St. Louis Fed) | REST, free key | primary for international series | Brent, WTI, LBMA gold, DGS10, DXY | US observation dates → next China session; research-use terms |

## 2. Added by plan 11 phase 10 (D-065)
| Source | Access | Role | What | Caveats |
|---|---|---|---|---|
| **AkShare** | Python library, no key | third source, gap-filler | foreign futures quotes FRED lacks (LME), official macro **release calendars** (replaces lag rules where available), CFFEX/SHFE/DCE/CZCE member position files | scrapes public pages; one decision per series; raw copies kept |
| **Exchange official files**: SSE, SZSE | CSV/XLS downloads (via AkShare or direct) | primary for lending eligibility and margin | 融资融券标的 lists (short-leg eligibility for ETF pairs), daily margin aggregates | file formats change; keep the downloaded file in `external/` with provenance |
| **BaoStock** | Python library, free login | verification only | daily closes and adjustment factors for A-shares | nightly cross-check vs Tushare `daily`/`adj_factor`; mismatches become `RISK_VALIDATION`-style quality rows, never overwrite |
| **NBS / PBOC** | official releases (via AkShare) | verification / release dates | CPI, PPI, PMI, M2 release dates | fixes `release_lag_days` approximations |

## 3. Candidates (not integrated; decision required)
| Source | Kind | Adds | Cost |
|---|---|---|---|
| Wind / iFinD / Choice | terminal + API | analyst consensus with history, industry classifications, daily index weights, events | institutional licence |
| Go-Goal (朝阳永续) | vendor API | consensus estimates, revisions, target prices; the China standard | licence |
| JoinQuant / RiceQuant data | API | minute bars, clean fundamentals | individual subscription |
| CSMAR / CNRDS | academic DB | governance, analyst, event studies | institutional |
| Hibor (慧博) | research report full text | text signals | licence |
| Yahoo Finance / Stooq | unofficial | HK/ADR prices, global indices | research only |
| EIA, LBMA, World Bank, IMF | official | oil fundamentals, gold fixings, macro | free |
| Tushare `stk_mins` / pytdx (通达信) | API / local files | intraday bars | tier / free |
Decision trigger for analyst data: the `report_rc` tier check (plan 11 ph7). If gated or thin, choose between no analyst family and licensing Go-Goal or a terminal.

## 4. Rules
- One `BaseApiClient` per source; `DatasetSpec.source` selects it; the same fetcher, writer, log and PIT rules apply (DATA_LOADING_DESIGN §3c).
- Verification sources never write to `raw/` datasets that a primary owns; they write to `raw/<source>_<dataset>/` and a quality view compares.
- Hand-downloaded files go to `external/<source>/` with a `PROVENANCE.md` (URL, date, who).
- Licence terms are recorded per source in this file before integration.
