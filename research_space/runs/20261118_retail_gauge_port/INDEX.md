# 20261118_retail_gauge_port

Plan 21 ph2–3 checks of the productionised RetailGauge against the v5 prototype (research_space/prototypes/holder_nowcast). Logged in `research_space/RESEARCH_LOG.md` (2026-11-18).

| File | Purpose |
|---|---|
| `feature_match.py` | RetailGaugeFeatureBuilder rows for 2026-11-12 vs the prototype panel, 20 sampled stocks: max abs difference per feature; `vintage` = lake as of the prototype run, `chips` = chip features vs the prototype snapshot file |
| `daily_rules.py` | D-167 rules on the production daily gauge (2023Q1–2026Q3, cap ≥ 50亿): retail_leaving holders-fell share and avoid_strong 60-session excess vs raw readings |
