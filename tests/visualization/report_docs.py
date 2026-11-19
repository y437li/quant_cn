"""Synthetic app documents for the morning-report tests (no real holdings)."""

from __future__ import annotations

from typing import Any

AS_OF = "20261112"


def _build_factor(factor: str, kind: str, d1: float, sigma: float, ratio: float) -> dict[str, Any]:
    ret = {"d1": d1, "w1": 0.01, "m1": -0.02, "m3": 0.0, "ytd": 0.05, "y1": 0.1}
    return {
        "factor": factor,
        "label": factor if kind != "industry" else "农林牧渔",
        "kind": kind,
        "ret": ret,
        "sigma_move": sigma,
        "vol_ratio": ratio,
        "forecast_vol": 0.1,
    }


def _build_holdings(as_of: str) -> dict[str, Any]:
    review = {
        "note": {"thesis": "t", "stop": 9.0, "target": 12.0},
        "flags": [{"kind": "stop", "message": "收盘 8.90 ≤ 止损 9.00"}],
        "chips": {"retail_gauge": 0.85},
        "period": "20260930",
        "conditions": [
            {
                "label": "毛利率 ≥ 22%",
                "kind": "statement",
                "metric": "gm_q",
                "op": ">=",
                "value": 0.22,
                "actual": 0.25,
                "state": "met",
            }
        ],
    }
    holdings = {
        "as_of": as_of,
        "model": "m",
        "benchmark": "000300.SH",
        "cash": 50000.0,
        "value": 1000000.0,
        "stock_value": 950000.0,
        "pnl": -50000.0,
        "risk": {"total": 0.16, "factor": 0.14, "specific": 0.08, "active_total": 0.13},
        "positions": [
            {"code": "600000.SH", "name": "示例甲", "weight": 0.55, "pnl_pct": 0.1, "contrib": 0.6},
            {
                "code": "000001.SZ",
                "name": "示例乙",
                "weight": 0.4,
                "pnl_pct": -0.2,
                "contrib": None,
            },
        ],
        "factors": [
            {
                "factor": "momentum",
                "label": "momentum",
                "kind": "style",
                "exposure": -0.5,
                "active": -0.5,
            }
        ],
        "reviews": {"600000.SH": review},
    }
    return holdings


def _build_factors(as_of: str) -> dict[str, Any]:
    return {
        "as_of": as_of,
        "model": "m",
        "factors": [
            _build_factor("country", "country", -0.01, -0.9, 1.0),
            _build_factor("beta", "style", 0.002, -2.4, 1.0),
            _build_factor("growth", "style", 0.001, 0.3, 1.7),
            _build_factor("ind_801010.SI", "industry", 0.012, 1.0, 1.0),
        ],
    }


def _build_watchlist(as_of: str) -> dict[str, Any]:
    entry = {
        "code": "600000.SH",
        "name": "示例甲",
        "price": 10.0,
        "buy_low": 9.0,
        "buy_high": 10.5,
        "gap_to_buy": 0.0,
        "conditions_needed": 1,
        "condition_status": "buy",
        "conditions": [{"label": "大单", "state": "met"}, {"label": "获利盘", "state": "unknown"}],
    }
    wait = entry | {
        "code": "000001.SZ",
        "name": "示例乙",
        "price": 20.0,
        "gap_to_buy": -0.1,
        "condition_status": "wait",
        "conditions": [],
        "conditions_needed": None,
    }
    return {"as_of": as_of, "entries": [wait, entry]}


def build_macro(new: bool = True) -> dict[str, Any]:
    """A two-line macro_monitor document; both lines new when `new`."""

    def line(
        key: str, name: str, unit: str, value: float, prev: float, pct: float
    ) -> dict[str, Any]:
        return {
            "key": key,
            "name": name,
            "group": "价格" if key == "cpi" else "社融",
            "unit": unit,
            "month": "202610",
            "value": value,
            "prev_month": "202609",
            "prev": prev,
            "change": round(value - prev, 2),
            "pct_5y": pct,
            "new_print": new,
            "history": [],
        }

    series = [
        line("cpi", "CPI 同比", "%", 0.7, 0.9, 0.6),
        line("sf_inc", "当月新增社融", "亿元", 35476.0, 16581.0, 0.95),
    ]
    return {
        "as_of": "202610",
        "missing": ["cn_m"],
        "new_prints": [s["key"] for s in series if new],
        "series": series,
    }


def build_docs(as_of: str = AS_OF) -> dict[str, dict[str, Any] | None]:
    """All five documents (no opportunities yet), one alert of each kind."""
    etf = {
        "as_of": as_of,
        "totals": {"core": {"position": 9000.0, "flow_ytd": -9500.0}},
        "recent": [{"date": as_of, "core": -28.0, "other": -6.0}],
    }
    return {
        "holdings_risk": _build_holdings(as_of),
        "factor_monitor": _build_factors(as_of),
        "etf_proxy": etf,
        "watchlist": _build_watchlist(as_of),
        "opportunities": None,
    }


def build_futures(new: bool = True) -> dict[str, Any]:
    """A one-family futures_monitor document with one curve signal (new when `new`)."""
    flag = {"key": "curve:CU.SHF", "kind": "curve", "name": "铜", "message": "近月升水 +3.8%"}
    return {
        "as_of": "20261113",
        "families": [{"family": "CU.SHF", "name": "铜"}],
        "spreads": [],
        "flags": [flag],
        "new_flags": [flag["key"]] if new else [],
        "missing": [],
    }
