# holder_nowcast — 股东户数（散户人数）季度预测原型

Research prototype from the 2026-11-12 session. It is not library code yet; productising it needs a plan (proposed plan 21). Scripts write and read data under `/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast/` (outside git). Run them with `uv run --with lightgbm --with scikit-learn python <script>`.

## Chosen model: 散户温度计 RetailGauge v5 (user, 2026-11-12: "以V5为准"; named 2026-11-13)

**Target.** y = ln(holders at quarter end / holders at the previous quarter end), from `stk_holdernumber`. It is ranked to a percentile within each quarter, so the model predicts each stock's cross-sectional rank.

**Model.** LightGBM regressor on within-quarter percentile ranks of 83 features. Parameters are in `lgbm_best.json`:
- n_estimators 800, learning_rate 0.05, num_leaves 63, min_child_samples 200;
- subsample 0.8, colsample_bytree 0.7, reg_lambda 1.

**Point-in-time protocol.**
- Expanding-window walk-forward by quarter.
- Training labels are used only if `ann_date` <= the prediction date.
- The `prev` / `prev2` lags are used only if announced.
- Medians come from the training data only.
- No target-based filtering of test rows.

**Features.** All use data on or before the as-of date.

| File | Content |
|---|---|
| `holders_v3_features.py` | Quarter path: returns, drawdown from highs, big up/down days, reversals, turnover level / change / acceleration / concentration, big-order flow and longest outflow run, margin change and run, size |
| `holders_v4_flow.py` | Order size split: large (20–100万) cumulative / last-20 / trend / runs, extra-large, small |
| `holders_v5_features.py` | Multi-scale windows of 5 / 20 / 60 / 120 days: turnover relative to its 1-year mean, returns, large-order flow, volatility, margin. EWMA with half-lives 5 / 20 / 60. 60-day slopes. Previous-quarter lags of key features |

The panel also uses chip snapshots: the chip distribution at each quarter end, pulled from Tushare `cyq_perf` into the lake runs folder as `cyq_qe.parquet`. It gives the winner rate, concentration, price versus median cost and the change in average cost.

**Results.** Walk-forward over 2022Q1–2026Q3 (19 quarters, about 5,000 stocks per quarter).

| Version | Rank IC mean / min | Top-decile → top-30% | Bottom-decile → bottom-30% |
|---|---|---|---|
| linear (13 features) | 0.47 / 0.35 | 69% | 58% |
| v3 LightGBM | 0.639 / 0.53 | 88% | 78% |
| v4 (+ order-size split) | 0.646 / 0.54 | 88% | 79% |
| **v5 (+ multi-scale / EWMA / slope / lags)** | **0.686 / 0.58** | **90%** | **82%** |
| v6 (+ national-team ETF flow via index weights) | 0.685 / 0.60 | 91% | — (no gain; not adopted) |

Checks:
- The leakage audit (point-in-time labels and lags) cost only 0.01 of IC.
- An industry-neutral target (SW L2 median removed) gave no gain over the raw target.

**Calibration.** `holders_calibration.csv` maps prediction deciles to the realised change relative to the quarter's market median:
- top decile: median +25%, IQR +14% to +42%;
- bottom decile: median −12%.
Typical Q4 market-wide median change: −1.7%.

**Drivers.** From mean |SHAP| and a depth-4 surrogate tree:
- Retail inflow: a recent turnover spike (5-day EWMA relative to the 1-year mean), especially with small-order net buying, or turnover rising while the price is far below its quarter high (dip buying).
- Retail outflow: turnover collapsing versus last quarter, with no acceleration.
- Holder inflows mean-revert in the following quarters.

## Files

| File | Purpose |
|---|---|
| `holders_v3_features.py` | builds v3 path features → `holders_v3_feats.parquet` |
| `holders_v4_flow.py` | order-size flow features → `holders_v4_flow.parquet` |
| `holders_v5_features.py` | multi-scale / EWMA / slope features → `holders_v5_feats.parquet` |
| `holders_v3_lgbm.py` | v3 panel assembly, labels and point-in-time lags; LightGBM tuning on validation quarters |
| `holders_v4_compare.py` | v3 vs v4 walk-forward |
| `holders_v5_compare.py` | v4 vs v5 walk-forward, nowcast, SHAP ranking |
| `holders_v5_forecast.py` | v5 calibration table and quarter-end holder forecast (`holders_forecast_q4.parquet`) |
| `holders_v5_shap.py` | per-stock SHAP drivers under v5 |
| `holders_rules.py` | depth-4 surrogate tree: readable feature-combination rules |
