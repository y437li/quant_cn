"""Top-20 broker nets per commodity family for the futures monitor (plan 15 ph7l, D-079)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_cn.calculation.futures_curve import SUFFIX_EXCHANGE
from quant_cn.core.futures_monitor_settings import FuturesMonitorSettings
from quant_cn.lake.lake_query import LakeQuery

FIVE_YEARS, WEEK = 1250, 5  # sessions
MIN_GROSS = 20_000  # lots (long + short): thinner families are shown but never flagged
_NETS = """
SELECT trade_date, exchange, regexp_extract(symbol, '^([A-Z]+)\\d{4}$', 1) AS code,
       sum(long_hld) AS long, sum(short_hld) AS short
FROM derived.fut_holding_brokers
WHERE trade_date >= ? AND regexp_matches(symbol, '^[A-Z]+\\d{4}$')
  AND list_contains(?, regexp_extract(symbol, '^([A-Z]+)\\d{4}$', 1))
GROUP BY 1, 2, 3
"""


class FuturesBrokerNets:
    """
    Purpose:
        Per watched commodity family: the top-20 brokers' summed long and short over the
        family's contracts (category rows already dropped by derived.fut_holding_brokers,
        D-079), the net (long - short) in lots, its share (long - short) / (long + short) so
        families of any size compare, the 5-day change of the share and its 5-year
        percentile. Top-20 figures are gross broker aggregates, not client intent.

    Contract:
        Input:
            settings: FuturesMonitorSettings  -- families
            query:    LakeQuery  -- derived.fut_holding_brokers
        Output:
            instance; `build(start)` -> {family: {net, gross, net_share, net_share_chg_5d,
            net_share_pct_5y}}, `list_flags(family, name, metrics)` -> flags
        Raises:
            (none at construction)

    Used by:
        calculation.FuturesMonitorBuilder  -- broker columns and flags per family

    Test cases:
        TC-FBN-001  sums only the family's contracts on its exchange; share, change, percentile
        TC-FBN-002  flag at the bounds names the extreme side; under MIN_GROSS lots no flag
        TC-FBN-003  without the derived view: {} and no query
    """

    def __init__(self, settings: FuturesMonitorSettings, query: LakeQuery) -> None:
        self._s = settings
        self._query = query

    def build(self, start: str) -> dict[str, dict[str, Any]]:
        """
        Purpose:
            Broker-net metrics on the last day with holdings, per family.

        Contract:
            Input:
                start: str  -- YYYYMMDD, first day read
            Output:
                dict  -- family -> {as_of, net, gross, net_share, net_share_chg_5d,
                         net_share_pct_5y}; {} when derived.fut_holding_brokers is missing;
                         families without holdings are left out
            Raises:
                LakeError  -- the query fails
        """
        if not self._query.has_view("derived.fut_holding_brokers"):
            return {}  # the view comes from curate (D-079); without it no broker columns
        codes = sorted({f.family.split(".")[0] for f in self._s.families})
        rows = self._query.sql(_NETS, [start, codes])
        rows = rows.assign(trade_date=rows["trade_date"].astype(str))
        out = {}
        for fam in self._s.families:
            code, _, suffix = fam.family.partition(".")
            mine = rows[(rows["code"] == code) & (rows["exchange"] == SUFFIX_EXCHANGE[suffix])]
            if mine.empty:
                continue
            out[fam.family] = self._build_summary(mine.sort_values("trade_date"))
        return out

    def list_flags(
        self, family: str, name: str, metrics: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """
        Purpose:
            A signal when a family's net share is at the 5-year percentile bounds.

        Contract:
            Input:
                family: str; name: str; metrics: one value of build or None
            Output:
                list[dict]  -- [] or one {key, kind "net", name, message}; never for families
                               under MIN_GROSS lots
            Raises:
                (none)
        """
        m = metrics or {}
        pct, share = m.get("net_share_pct_5y"), m.get("net_share")
        if pct is None or share is None or (m.get("gross") or 0) < MIN_GROSS:
            return []
        if self._s.flag_low < pct < self._s.flag_high:
            return []
        side = "偏多到 5 年最高" if pct >= self._s.flag_high else "偏空到 5 年最深"
        text = f"前20名净持仓 {m['net']:+,.0f} 手（多空差 {share * 100:+.1f}%），{side}"
        return [{"key": f"net:{family}", "kind": "net", "name": name, "message": text}]

    @staticmethod
    def _build_summary(rows: pd.DataFrame) -> dict[str, Any]:
        long, short = rows["long"].fillna(0.0), rows["short"].fillna(0.0)
        share = ((long - short) / (long + short)).reset_index(drop=True)
        window = share.dropna().iloc[-FIVE_YEARS:]
        last = share.iloc[-1]
        chg = last - share.iloc[-1 - WEEK] if len(share) > WEEK else None
        return {
            "as_of": str(rows["trade_date"].iloc[-1]),
            "net": round(float(long.iloc[-1] - short.iloc[-1]), 0),
            "gross": round(float(long.iloc[-1] + short.iloc[-1]), 0),
            "net_share": None if pd.isna(last) else round(float(last), 4),
            "net_share_chg_5d": None if chg is None or pd.isna(chg) else round(float(chg), 4),
            "net_share_pct_5y": None
            if window.empty or pd.isna(last)
            else round(float((window <= last).mean()), 3),
        }
