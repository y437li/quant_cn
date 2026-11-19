# 20261118_shekou_bollinger

Does 招商蛇口 mean-revert at its Bollinger bands (20-day, 2σ)? Peers 保利 / 万科 / 华发 / 金地 as a check. Logged in `research_space/RESEARCH_LOG.md` (2026-11-18).

| File | Purpose |
|---|---|
| `bollinger_reversion.py` | first close below the lower / above the upper band on `derived.prices_adj`; forward 5/10/20-session returns, raw and in excess of 申万房地产 (801180.SI), hit rate of the middle band, worst 20-session move; daily return autocorrelation; current band levels |
| `lower_band_variants.py` | lower-band variants (2 / 2.5 / 3σ touch, two closes below, re-entry within 10 sessions), 5–60 session horizons, events ≥ 10 sessions apart, 蛇口 alone / five pooled / from 2023 |
