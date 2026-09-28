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
    Raises:
        (none)

Used by:
    (none yet)  -- produced by LakeQuery.prices and PitAligner (plan 01 phase 5)

Test cases:
    TC-FR-003  VIX_PANEL declares text columns and key; an empty frame validates
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
