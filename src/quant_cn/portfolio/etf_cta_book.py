"""ETF CTA book document behind the app page and e-mail (plan 27, D-160)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.core.date_codec import DateCodec
from quant_cn.core.etf_cta_settings import EtfCtaSettings
from quant_cn.core.etf_cta_views import EtfCtaViews
from quant_cn.core.exceptions import LakeError
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.portfolio.etf_cta_paper_book import EtfCtaPaperBook
from quant_cn.portfolio.etf_cta_record import EtfCtaRecord
from quant_cn.portfolio.etf_cta_view_tilt import EtfCtaViewTilt
from quant_cn.portfolio.etf_cta_weights import EtfCtaWeights

FILE_NAME = "etf_cta.json"
WARM_UP_DAYS = 600  # calendar days loaded before history_start (252-session signals, 60-day vols)
CLIP = 0.2  # daily returns beyond ±20% are data errors
EPS = 1e-9  # weights closer than this are equal
_PRICES = """
SELECT ts_code, trade_date, close, pre_close FROM curated.fund_daily
WHERE list_contains(?, ts_code) AND trade_date >= ? AND pre_close > 0 ORDER BY trade_date
"""
_NAV = """
SELECT n.ts_code, n.nav_date, any_value(n.unit_nav) AS nav, any_value(p.close) AS close
FROM curated.fund_nav n JOIN curated.fund_daily p
  ON p.ts_code = n.ts_code AND p.trade_date = n.nav_date
WHERE list_contains(?, n.ts_code) AND n.nav_date >= ? AND n.unit_nav > 0
GROUP BY 1, 2 ORDER BY 2
"""


class EtfCtaBook:
    """
    Purpose:
        Build `etf_cta.json`: the latest weekly decision of the ETF CTA book (target and held
        weight per ETF, the trade to make, group totals and their change against the previous
        week, the signals behind them), the premium guard (no adds to a guarded QDII / LOF at or
        above buy_below), flags, the back-test record from history_start and the paper book from
        paper_start, both run with the no-trade band and costs; and the 含观点 track (D-163):
        the same targets tilted by the user's views, with its own rows and paper record.

    Contract:
        Input:
            settings: EtfCtaSettings
            query:    LakeQuery   -- reads curated.fund_daily and curated.fund_nav
            codec:    DateCodec
            weights:  EtfCtaWeights | None    -- None = built from settings
            paper:    EtfCtaPaperBook | None  -- None = built from settings (band, cost)
            views:    EtfCtaViews | None      -- None = no views (the two tracks are equal)
        Output:
            instance; `build(previous)` -> dict; `write(out_dir)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `etf-cta` command

    Test cases:
        TC-ECB-001  document lists every ETF with target, held, trade and action, groups summed
        TC-ECB-002  a guarded ETF at or above buy_below is not bought; state and flag shown
        TC-ECB-003  back-test and paper records start at their dates; paper starts in cash
        TC-ECB-004  a group change at group_step is flagged; new_flags only once
        TC-ECB-005  no fund_daily rows raises LakeError; write needs an existing directory
        TC-ECB-006  with no views both tracks are equal; a live view tilts the 含观点 rows and
                    paper, lists the view and adds its flags
    """

    def __init__(
        self,
        settings: EtfCtaSettings,
        query: LakeQuery,
        codec: DateCodec,
        weights: EtfCtaWeights | None = None,
        paper: EtfCtaPaperBook | None = None,
        views: EtfCtaViews | None = None,
    ) -> None:
        self._s = settings
        self._query = query
        self._codec = codec
        self._weights = weights or EtfCtaWeights(settings)
        groups = {c: g.name for g in settings.groups for c in g.members}
        groups |= {c: "债券" for c in settings.bonds}
        self._paper = paper or EtfCtaPaperBook(settings.band, settings.cost, groups)
        self._views = views or EtfCtaViews()
        self._full = EtfCtaWeights(settings.model_copy(update={"timed": []}))
        self._tilt = EtfCtaViewTilt(settings, codec)
        self._record = EtfCtaRecord(codec)

    def build(self, previous: dict[str, Any] | None) -> dict[str, Any]:
        """
        Purpose:
            The book document as of the last session in curated.fund_daily.

        Contract:
            Input:
                previous: dict | None  -- the last written document (for new_flags)
            Output:
                dict  -- {as_of, decision_date, weights: [...], groups: [...], cash, signals,
                         premium: [...], flags: [...], new_flags: [...], backtest, paper,
                         views: {floor, items, groups, weights: [...], paper}};
                         weights and returns as fractions
            Raises:
                LakeError  -- no prices for the configured ETFs
        """
        returns, cash, closes = self._read_returns()
        targets = self._weights.compute_targets(returns)
        decision = targets.index[-1]
        premium = self._read_premium()
        blocked = [p["code"] for p in premium if p["blocked"]]
        no_add = {decision: blocked}
        paper_start = max(self._to_stamp(self._s.paper_start), targets.index[0])
        paper = self._paper.run(returns, cash, targets, min(paper_start, decision), no_add)
        back = self._paper.run(
            returns, cash, targets, self._to_stamp(self._s.history_start), no_add
        )
        rows = self._build_rows(targets, paper, decision)
        groups = self._build_groups(rows)
        views = self._build_views(
            returns, cash, closes, targets, min(paper_start, decision), no_add
        )
        flags = self._list_flags(groups, premium, decision) + views.pop("flags")
        old = {f["key"] for f in (previous or {}).get("flags", [])}
        return {
            "as_of": self._codec.to_str(returns.index[-1].date()),
            "decision_date": self._codec.to_str(decision.date()),
            "settings": {
                k: getattr(self._s, k) for k in ("risk_share", "bond_share", "band", "cost")
            },
            "weights": rows,
            "groups": groups,
            "signals": self._weights.build_summary(returns),
            "premium": premium,
            "flags": flags,
            "new_flags": [f["key"] for f in flags if f["key"] not in old],
            "backtest": self._record.build(self._to_series(back["nav"]), cash),
            "paper": self._record.build(self._to_series(paper["nav"]), cash),
            "views": views,
        }

    def _build_views(
        self,
        returns: pd.DataFrame,
        cash: pd.Series,
        closes: pd.DataFrame,
        targets: pd.DataFrame,
        start: pd.Timestamp,
        no_add: dict[pd.Timestamp, list[str]],
    ) -> dict[str, Any]:
        floor = self._views.a_share_floor is not None
        full = self._full.compute_targets(returns) if floor else None
        tilted = self._tilt.compute_targets(targets, self._views, closes, full)
        paper = self._paper.run(returns, cash, tilted, start, no_add)
        out = self._tilt.build_summary(targets, tilted, self._views, closes)
        out["weights"] = self._build_rows(tilted, paper, pd.Timestamp(targets.index[-1]))
        out["paper"] = self._record.build(self._to_series(paper["nav"]), cash)
        return out

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build against the previous `etf_cta.json` in out_dir and overwrite it.

        Contract:
            Input:
                out_dir: Path  -- existing directory
            Output:
                Path  -- the written file
            Raises:
                LakeError  -- out_dir missing, or as build
        """
        if not out_dir.is_dir():
            raise LakeError(f"output directory {out_dir} does not exist")
        path = out_dir / FILE_NAME
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        doc = self.build(previous)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        return path

    def _read_returns(self) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
        start = self._codec.to_date(self._s.history_start) - pd.Timedelta(days=WARM_UP_DAYS)
        raw = self._query.sql(_PRICES, [self._s.list_codes(), self._codec.to_str(start)])
        if raw.empty:
            raise LakeError(
                "curated.fund_daily has no rows for the ETF CTA book: run make etf-proxy"
            )
        raw["ret"] = (raw["close"] / raw["pre_close"] - 1.0).clip(-CLIP, CLIP)
        panel = raw.pivot_table(
            index="trade_date", columns="ts_code", values="ret", aggfunc="first"
        )
        closes = raw.pivot_table(
            index="trade_date", columns="ts_code", values="close", aggfunc="first"
        )
        for frame in (panel, closes):
            frame.index = pd.DatetimeIndex([self._to_stamp(str(d)) for d in frame.index])
        panel = panel.sort_index().reindex(columns=self._s.list_codes())
        cash = panel.pop(self._s.cash).fillna(0.0)
        return panel, cash, closes.sort_index()

    def _read_premium(self) -> list[dict[str, Any]]:
        p = self._s.premium
        if not p.codes:
            return []
        start = self._codec.to_date(self._s.paper_start) - pd.Timedelta(days=90)
        nav = self._query.sql(_NAV, [p.codes, self._codec.to_str(start)])
        out = []
        for code in p.codes:
            rows = nav[nav["ts_code"] == code]
            row: dict[str, Any] = {"code": code, "name": self._s.names.get(code, code),
                                   "premium": None, "nav_date": None, "state": "未知",
                                   "blocked": False, "alternative": ""}  # fmt: skip
            if not rows.empty:
                last = rows.iloc[-1]
                value = float(last["close"] / last["nav"] - 1.0)
                row["premium"], row["nav_date"] = round(value, 4), str(last["nav_date"])
                row["state"] = (
                    "可买" if value < p.buy_below else ("很高" if value >= p.high else "偏高")
                )
                row["blocked"] = value >= p.buy_below
                row["alternative"] = p.alternative.get(code, "") if value >= p.switch else ""
            out.append(row)
        return out

    def _build_rows(
        self,
        targets: pd.DataFrame,
        paper: dict[str, pd.DataFrame | pd.Series],
        decision: pd.Timestamp,
    ) -> list[dict[str, Any]]:
        group_of = {c: g.name for g in self._s.groups for c in g.members}
        group_of |= {c: "债券" for c in self._s.bonds}
        weights = pd.DataFrame(paper["weights"])
        trades = pd.DataFrame(paper["trades"])
        before = weights.loc[weights.index < decision]
        held = before.iloc[-1] if not before.empty else pd.Series(0.0, index=weights.columns)
        trade = trades.reindex(index=[decision], columns=targets.columns).fillna(0.0).iloc[0]
        last = targets.iloc[-2] if len(targets) > 1 else targets.iloc[-1] * 0.0
        rows = []
        for code in [*targets.columns, self._s.cash]:
            is_cash = code == self._s.cash
            now = targets.iloc[-1]
            target = (1.0 - float(now.sum())) if is_cash else float(now.loc[code])
            prev = (1.0 - float(last.sum())) if is_cash else float(last[code])
            h = float(held["cash"] if is_cash else held[code])
            t = -float(trade.sum()) if is_cash else float(trade[code])
            rows.append(
                {
                    "code": code,
                    "name": self._s.names.get(code, code),
                    "group": "现金" if is_cash else group_of[code],
                    "target": round(target, 4),
                    "last_target": round(prev, 4),
                    "held": round(h, 4),
                    "trade": round(t, 4),
                    "action": "买入" if t > EPS else ("卖出" if t < -EPS else "不动"),
                }
            )
        return rows

    def _build_groups(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        names = [g.name for g in self._s.groups] + ["债券", "现金"]
        out = []
        for name in names:
            part = [r for r in rows if r["group"] == name]
            if not part:
                continue
            target = sum(r["target"] for r in part)
            last = sum(r["last_target"] for r in part)
            out.append(
                {
                    "name": name,
                    "target": round(target, 4),
                    "last_target": round(last, 4),
                    "change": round(target - last, 4),
                }
            )
        return out

    def _list_flags(
        self, groups: list[dict[str, Any]], premium: list[dict[str, Any]], decision: pd.Timestamp
    ) -> list[dict[str, Any]]:
        day = self._codec.to_str(decision.date())
        flags = [
            {
                "key": f"group:{g['name']}:{day}",
                "kind": "group",
                "message": f"{g['name']}目标权重{'升' if g['change'] > 0 else '降'}了"
                f"{abs(g['change']) * 100:.1f}个百分点 ({g['last_target'] * 100:.1f}% → "
                f"{g['target'] * 100:.1f}%)",
            }
            for g in groups
            if abs(g["change"]) >= self._s.group_step - EPS
        ]
        for p in premium:
            if p["blocked"]:
                alt = (
                    f", 可考虑{self._s.names.get(p['alternative'], p['alternative'])}"
                    if p["alternative"]
                    else ""
                )
                flags.append(
                    {
                        "key": f"premium:{p['code']}:{p['state']}",
                        "kind": "premium",
                        "message": f"{p['name']}溢价{p['premium'] * 100:.1f}%({p['state']}), "
                        f"本周不加仓{alt}",
                    }
                )
        return flags

    @staticmethod
    def _to_series(value: pd.DataFrame | pd.Series) -> pd.Series:
        return value if isinstance(value, pd.Series) else value.iloc[:, 0]

    def _to_stamp(self, value: str) -> pd.Timestamp:
        return pd.Timestamp(self._codec.to_date(value))
