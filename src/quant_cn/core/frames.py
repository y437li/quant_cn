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
    Raises:
        (none)

Used by:
    (none yet)  -- produced by LakeQuery.prices and PitAligner (plan 01 phase 5)

Test cases:
    TC-FR-003  VIX_PANEL declares text columns and key; an empty frame validates
    TC-FR-004  plan 09 frames (GEX_PANEL, FUTURES_POSITIONING, MARGIN_*) validate empty frames
    TC-FR-001  each frame's key and text columns are declared columns; empty frames validate
    TC-FR-002  a frame with a duplicate key fails validation
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
