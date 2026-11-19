"""股指期货 part of the futures monitor: basis and top-20 broker nets (plan 15 ph7k)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_cn.calculation.futures_positioning import FuturesPositioning
from quant_cn.core.futures_monitor_settings import FuturesMonitorSettings
from quant_cn.lake.lake_query import LakeQuery

FIVE_YEARS, WEEK = 1250, 5  # sessions
_DAILY = """
SELECT ts_code, trade_date, close, oi FROM derived.fut_daily_one_sided
WHERE regexp_matches(ts_code, ?) AND trade_date >= ?
"""
_HOLDING = """
SELECT trade_date, symbol, broker, long_hld, short_hld FROM derived.fut_holding_brokers
WHERE exchange = 'CFFEX' AND regexp_matches(symbol, ?) AND trade_date >= ?
"""
_SPOT = "SELECT trade_date, close FROM curated.index_daily WHERE ts_code = ? AND trade_date >= ?"


class IndexFuturesMonitor:
    """
    Purpose:
        For each CFFEX index-futures product (IF, IH, IC, IM): run plan 09's FuturesPositioning
        over five years and summarise the last day: main-contract basis to the index (raw and
        annualised to its third-Friday expiry) with its 5-year percentile, top-20 broker net
        (long − short) with its 5-day change and 5-year percentile, total OI with its 5-day
        change, and the OI × price regime; weekly histories of the annualised basis and the net.
        Flags when the annualised basis or the net is at or beyond the percentile bounds.

    Contract:
        Input:
            settings: FuturesMonitorSettings  -- index_futures, flag_low, flag_high
            query:    LakeQuery  -- derived.fut_daily_one_sided, derived.fut_holding_brokers,
                                    curated.index_daily
        Output:
            instance; `build(start)` -> {products, flags, missing}
        Raises:
            (none at construction)

    Used by:
        calculation.FuturesMonitorBuilder  -- `index_futures` part of futures_monitor.json

    Test cases:
        TC-IFM-001  last-day basis, net and percentiles from a hand positioning frame
        TC-IFM-002  a flag fires at the bound and not just inside; a product without rows is
                    listed as missing
    """

    def __init__(self, settings: FuturesMonitorSettings, query: LakeQuery) -> None:
        self._s = settings
        self._query = query

    def build(self, start: str) -> dict[str, Any]:
        """
        Purpose:
            The 股指期货 part of the futures monitor from `start` on.

        Contract:
            Input:
                start: str  -- YYYYMMDD, first day read (five years before the last session)
            Output:
                dict  -- {products: [{product, name, index, as_of, main_contract, price, spot,
                         basis_pct, basis_annualised, basis_pct_5y, net, net_chg_5d, net_pct_5y,
                         oi, oi_chg_5d, regime, history: [{d, basis, net}]}], flags: [...],
                         missing: [product]}; basis in percent; every product missing when
                         the derived views do not exist
            Raises:
                LakeError  -- a query fails
        """
        products, flags, missing = [], [], []
        if not self._query.has_view("derived.fut_daily_one_sided"):
            names = [p.product for p in self._s.index_futures]
            return {"products": [], "flags": [], "missing": names}
        for p in self._s.index_futures:
            pattern = rf"^{p.product}\d{{4}}"
            daily = self._query.sql(_DAILY, [pattern, start])
            if daily.empty:
                missing.append(p.product)
                continue
            holding = self._query.sql(_HOLDING, [pattern + "$", start])
            spot = self._query.sql(_SPOT, [p.index, start]).set_index("trade_date")["close"]
            frame = FuturesPositioning(p.product).compute(daily, holding, spot)
            row = self.build_product(p.product, p.name, p.index, frame)
            products.append(row)
            flags += self.list_flags(row)
        return {"products": products, "flags": flags, "missing": missing}

    def build_product(
        self, product: str, name: str, index: str, frame: pd.DataFrame
    ) -> dict[str, Any]:
        """
        Purpose:
            The summary of one product from its FuturesPositioning frame.

        Contract:
            Input:
                product, name, index: str; frame: FUTURES_POSITIONING rows, sorted by date
            Output:
                dict  -- as one `products` item of build
            Raises:
                (none)
        """
        f = frame.sort_values("trade_date").reset_index(drop=True)
        last = f.iloc[-1]
        net, oi, more = f["top20_net"], f["oi_total"], len(f) > WEEK
        net_chg = net.iloc[-1] - net.iloc[-1 - WEEK] if more else None
        oi_chg = oi.iloc[-1] / oi.iloc[-1 - WEEK] - 1 if more else None
        hist = f.iloc[-FIVE_YEARS:].iloc[::-1].iloc[::WEEK].iloc[::-1]
        return {
            "product": product,
            "name": name,
            "index": index,
            "as_of": str(last["trade_date"]),
            "main_contract": str(last["main_contract"]),
            "price": self._to_number(last["price"], 2),
            "spot": self._to_number(last["spot"], 2),
            "basis_pct": self._to_number(last["basis_pct"], 3),
            "basis_annualised": self._to_number(last["basis_annualised"], 2),
            "basis_pct_5y": self._compute_pct(f["basis_annualised"]),
            "net": self._to_number(last["top20_net"], 0),
            "net_chg_5d": self._to_number(net_chg, 0),
            "net_pct_5y": self._compute_pct(net),
            "oi": self._to_number(last["oi_total"], 0),
            "oi_chg_5d": self._to_number(oi_chg, 4),
            "regime": str(last["regime"]),
            "history": [
                {
                    "d": str(r.trade_date),
                    "basis": self._to_number(r.basis_annualised, 2),
                    "net": self._to_number(r.top20_net, 0),
                }
                for r in hist.itertuples()
            ],
        }

    def list_flags(self, row: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Purpose:
            Signals of one product: annualised basis or top-20 net at the percentile bounds.

        Contract:
            Input:
                row: one `products` item
            Output:
                list[dict]  -- {key, kind, name, message}
            Raises:
                (none)
        """
        out = []
        lo, hi = self._s.flag_low, self._s.flag_high
        pct, v = row["basis_pct_5y"], row["basis_annualised"]
        if pct is not None and v is not None and (pct <= lo or pct >= hi):
            side = "贴水最深" if pct <= lo else "升水最高"
            text = f"年化基差 {v:+.1f}%，5年 {pct * 100:.0f}% 分位（{side}）"
            out.append({"key": f"basis:{row['product']}", "kind": "basis",
                        "name": f"{row['name']}股指期货", "message": text})  # fmt: skip
        pct, n = row["net_pct_5y"], row["net"]
        if pct is not None and n is not None and (pct <= lo or pct >= hi):
            text = f"前20名净持仓 {n:+,.0f} 手，5年 {pct * 100:.0f}% 分位"
            out.append({"key": f"net:{row['product']}", "kind": "net",
                        "name": f"{row['name']}股指期货", "message": text})  # fmt: skip
        return out

    @staticmethod
    def _compute_pct(series: pd.Series) -> float | None:
        values = series.dropna().iloc[-FIVE_YEARS:]
        if values.empty or pd.isna(series.iloc[-1]):
            return None
        return round(float((values <= values.iloc[-1]).mean()), 3)

    @staticmethod
    def _to_number(v: Any, digits: int) -> float | None:
        if v is None or pd.isna(v):
            return None
        return round(float(v), digits)
