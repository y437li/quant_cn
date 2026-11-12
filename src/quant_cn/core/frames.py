"""Shared panel schemas that cross package boundaries (SRC_DESIGN §3); long format, YYYYMMDD dates.

Purpose:
    One registered Schema per frame exchanged between packages, so producers validate and
    consumers trust the shape.

Contract:
    Input:
        (module of constants)
    Output:
        PRICE_PANEL       -- key (trade_date, ts_code); OHLC, pre_close, vol, amount,
                             adj_factor, close_adj
        FUNDAMENTALS_PIT  -- key (trade_date, ts_code, field); value, end_date, ann_date
        VIX_PANEL         -- key (trade_date, underlying); vix and its per-term inputs
        GEX_PANEL         -- key (trade_date, maturity_date, strike, call_put); gamma per option
        FUTURES_POSITIONING -- key (trade_date, product); OI regime, top-20 net, basis
        MARGIN_VINTAGES   -- key (ts_code, entry_date, seeded); FIFO financing vintages
        MARGIN_LADDER     -- key (drawdown_pct); financing debt forced at each market drawdown
        UNIVERSE_PANEL    -- key (trade_date, ts_code); in_universe (1/0), reason
        FACTOR_PANEL      -- key (trade_date, ts_code, factor); value, value_raw
        IC_SERIES         -- key (trade_date, factor, horizon); ic, n
        IC_TEST           -- key (factor, horizon, metric, window); value, se, t, p, CI, adjusted p
        TRIAL_LOG         -- key (campaign, trial_id); factor, params, horizon, sr, ic_mean
        FORWARD_RETURN    -- key (trade_date, ts_code, horizon); fwd_return (open t+1 -> close t+h)
        QUANTILE_RETURNS  -- key (trade_date, factor, horizon, quantile); ret, n
                             (quantile 0 = long-short)
        EXPOSURE_PANEL    -- key (trade_date, ts_code); Shenwan L1 group, backfilled flag, log mcap
        RISK_EXPOSURE     -- key (trade_date, ts_code, factor); exposure, exposure_raw, is_filled
        FACTOR_RETURN     -- key (trade_date, factor); ret, t_stat, r2, n_obs
        SPECIFIC_RETURN   -- key (trade_date, ts_code); resid, weight (regression; 0 = outside)
        FACTOR_COV        -- key (trade_date, factor_i, factor_j); cov, cov_raw, horizon_days
        SPECIFIC_RISK     -- key (trade_date, ts_code); sigma, sigma_raw, method
        RISK_DECOMP       -- key (trade_date, portfolio, component); risk, pct, kind
        RISK_VALIDATION   -- key (trade_date, metric, scope); value, window, notes
    Raises:
        (none)

Used by:
    (none yet)  -- produced by LakeQuery.prices and PitAligner (plan 01 phase 5)

Test cases:
    TC-FR-003  VIX_PANEL declares text columns and key; an empty frame validates
    TC-FR-004  plan 09 frames (GEX_PANEL, FUTURES_POSITIONING, MARGIN_*) validate empty frames
    TC-FR-001  each frame's key and text columns are declared columns; empty frames validate
    TC-FR-002  a frame with a duplicate key fails validation
    TC-FR-005  plan 04 frames (UNIVERSE_PANEL ... EXPOSURE_PANEL) validate a one-row frame
    TC-FR-006  plan 05 risk frames validate a one-row frame and reject duplicate keys
"""

from __future__ import annotations

from typing import Final

from quant_cn.core.schema import Schema

PRICE_PANEL: Final = Schema(
    "PRICE_PANEL",
    columns=[
        "trade_date",
        "ts_code",
        "open",
        "high",
        "low",
        "close",
        "pre_close",
        "vol",
        "amount",
        "adj_factor",
        "close_adj",
    ],
    text_columns=["trade_date", "ts_code"],
    primary_key=["trade_date", "ts_code"],
)

FUNDAMENTALS_PIT: Final = Schema(
    "FUNDAMENTALS_PIT",
    columns=["trade_date", "ts_code", "field", "value", "end_date", "ann_date"],
    text_columns=["trade_date", "ts_code", "field", "end_date", "ann_date"],
    primary_key=["trade_date", "ts_code", "field"],
)

VIX_PANEL: Final = Schema(
    "VIX_PANEL",
    columns=[
        "trade_date",
        "underlying",
        "clock",
        "vix",
        "var_near",
        "var_next",
        "days_near",
        "days_next",
        "t_near",
        "t_next",
        "f_near",
        "f_next",
        "k0_near",
        "k0_next",
        "n_options_near",
        "n_options_next",
        "rate_near",
        "rate_next",
        "quality_flag",
    ],
    text_columns=["trade_date", "underlying", "clock", "quality_flag"],
    primary_key=["trade_date", "underlying"],
)

GEX_PANEL: Final = Schema(
    "GEX_PANEL",
    columns=[
        "trade_date",
        "maturity_date",
        "days",
        "strike",
        "call_put",
        "oi",
        "price",
        "forward",
        "rate",
        "t",
        "iv",
        "gamma",
        "sign",
        "multiplier",
        "gex",
    ],
    text_columns=["trade_date", "maturity_date", "call_put"],
    primary_key=["trade_date", "maturity_date", "strike", "call_put"],
)

FUTURES_POSITIONING: Final = Schema(
    "FUTURES_POSITIONING",
    columns=[
        "trade_date",
        "product",
        "main_contract",
        "price",
        "price_change",
        "oi_total",
        "oi_change",
        "regime",
        "top20_long",
        "top20_short",
        "top20_net",
        "spot",
        "basis_pct",
        "basis_annualised",
    ],
    text_columns=["trade_date", "product", "main_contract", "regime"],
    primary_key=["trade_date", "product"],
)

MARGIN_VINTAGES: Final = Schema(
    "MARGIN_VINTAGES",
    columns=[
        "ts_code",
        "entry_date",
        "entry_price",
        "debt",
        "liquidation_price",
        "price",
        "distance_pct",
        "seeded",
    ],
    text_columns=["ts_code", "entry_date"],
    primary_key=["ts_code", "entry_date", "seeded"],
)

MARGIN_LADDER: Final = Schema(
    "MARGIN_LADDER",
    columns=["drawdown_pct", "debt_forced", "share_of_debt"],
    text_columns=[],
    primary_key=["drawdown_pct"],
)

# --- plan 04 (factors): universe, factor values, IC and test results, trial log ---

UNIVERSE_PANEL: Final = Schema(
    "UNIVERSE_PANEL",
    columns=["trade_date", "ts_code", "in_universe", "reason"],
    text_columns=["trade_date", "ts_code", "reason"],
    primary_key=["trade_date", "ts_code"],
)

FACTOR_PANEL: Final = Schema(
    "FACTOR_PANEL",
    columns=["trade_date", "ts_code", "factor", "value", "value_raw"],
    text_columns=["trade_date", "ts_code", "factor"],
    primary_key=["trade_date", "ts_code", "factor"],
)

IC_SERIES: Final = Schema(
    "IC_SERIES",
    columns=["trade_date", "factor", "horizon", "ic", "n"],
    text_columns=["trade_date", "factor"],
    primary_key=["trade_date", "factor", "horizon"],
)

IC_TEST: Final = Schema(
    "IC_TEST",
    columns=[
        "factor",
        "horizon",
        "metric",
        "value",
        "se",
        "t",
        "p",
        "ci_lo",
        "ci_hi",
        "window",
        "p_adj_holm",
        "p_adj_bhy",
        "p_adj_romano_wolf",
        "hlz_pass",
    ],
    text_columns=["factor", "metric", "window"],
    primary_key=["factor", "horizon", "metric", "window"],
)

TRIAL_LOG: Final = Schema(
    "TRIAL_LOG",
    columns=["campaign", "trial_id", "factor", "params", "horizon", "sr", "ic_mean"],
    text_columns=["campaign", "trial_id", "factor", "params"],
    primary_key=["campaign", "trial_id"],
)

FORWARD_RETURN: Final = Schema(
    "FORWARD_RETURN",
    columns=["trade_date", "ts_code", "horizon", "fwd_return"],
    text_columns=["trade_date", "ts_code"],
    primary_key=["trade_date", "ts_code", "horizon"],
)

QUANTILE_RETURNS: Final = Schema(
    "QUANTILE_RETURNS",
    columns=["trade_date", "factor", "horizon", "quantile", "ret", "n"],
    text_columns=["trade_date", "factor"],
    primary_key=["trade_date", "factor", "horizon", "quantile"],
)

EXPOSURE_PANEL: Final = Schema(
    "EXPOSURE_PANEL",
    columns=["trade_date", "ts_code", "l1_code", "industry_backfilled", "log_mcap"],
    text_columns=["trade_date", "ts_code", "l1_code"],
    primary_key=["trade_date", "ts_code"],
)

# plan 05 risk model (RISK_MODEL_DESIGN §4; SPECIFIC_RETURN added by D-127 for incremental refits)
RISK_EXPOSURE: Final = Schema(
    "RISK_EXPOSURE",
    columns=["trade_date", "ts_code", "factor", "exposure", "exposure_raw", "is_filled"],
    text_columns=["trade_date", "ts_code", "factor"],
    primary_key=["trade_date", "ts_code", "factor"],
)

FACTOR_RETURN: Final = Schema(
    "FACTOR_RETURN",
    columns=["trade_date", "factor", "ret", "t_stat", "r2", "n_obs"],
    text_columns=["trade_date", "factor"],
    primary_key=["trade_date", "factor"],
)

SPECIFIC_RETURN: Final = Schema(
    "SPECIFIC_RETURN",
    columns=["trade_date", "ts_code", "resid", "weight"],
    text_columns=["trade_date", "ts_code"],
    primary_key=["trade_date", "ts_code"],
)

FACTOR_COV: Final = Schema(
    "FACTOR_COV",
    columns=["trade_date", "factor_i", "factor_j", "cov", "cov_raw", "horizon_days"],
    text_columns=["trade_date", "factor_i", "factor_j"],
    primary_key=["trade_date", "factor_i", "factor_j"],
)

SPECIFIC_RISK: Final = Schema(
    "SPECIFIC_RISK",
    columns=["trade_date", "ts_code", "sigma", "sigma_raw", "method"],
    text_columns=["trade_date", "ts_code", "method"],
    primary_key=["trade_date", "ts_code"],
)

RISK_DECOMP: Final = Schema(
    "RISK_DECOMP",
    columns=["trade_date", "portfolio", "component", "risk", "pct", "kind"],
    text_columns=["trade_date", "portfolio", "component", "kind"],
    primary_key=["trade_date", "portfolio", "component"],
)

RISK_VALIDATION: Final = Schema(
    "RISK_VALIDATION",
    columns=["trade_date", "metric", "scope", "value", "window", "notes"],
    text_columns=["trade_date", "metric", "scope", "window", "notes"],
    primary_key=["trade_date", "metric", "scope"],
)
