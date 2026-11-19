"""Buyback programmes and 增持 plans joined to their buyback_terms labels (plan 32 ph3, D-169)."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

START = "20240101"  # programmes and plans announced before this are left out
MATCH_DAYS = 3  # a label or a 限制性股票 title within this many days of a 预案 belongs to it
LABEL_DAYS = 90  # a later 回购报告书 up to this many days after the 预案 still labels it
INCREASE_MONTHS = 6  # period of a 增持 plan that gives none
FRAME_COLUMNS = [
    "kind", "code", "date", "end", "state", "tags", "holders", "funding", "loan_bank",
    "loan_amount", "low", "high", "executed", "executed_before", "price_cap", "labelled",
]  # fmt: skip
_ITEM_FIELDS = ("kind", "purpose", "holder_type", "holders", "funding", "loan_bank", "loan_amount",
                "amount_low", "amount_high", "shares_low", "shares_high", "price_cap",
                "period_months")  # fmt: skip


class BuybackPlanFrame:
    """
    Purpose:
        Put both kinds of programme in one frame, one row each, with the label fields.
        回购: BuybackLedger programmes announced since START (seeded ones dropped). Each takes
        the buyback_terms 回购 labels of its stock announced from MATCH_DAYS before its 预案 up
        to LABEL_DAYS after it, and before the next 预案 (the 方案 and the later 报告书 both
        label it). The earliest label gives purpose, amounts and price cap; funding is the union
        of all of them; loan bank and amount come from any of them. An unlabelled programme
        stays only when no 限制性股票 title is within MATCH_DAYS (restricted-stock 回购注销 is
        not a market programme) and it has a price cap. 增持: one row per 增持 label item, with
        the 方案 / 报告书 repeat of the same holders and amounts dropped; it runs from its
        announcement for period_months (INCREASE_MONTHS when none); executed = Σ change_vol x
        (avg_price, else that day's close) of the named holders' IN trades disclosed inside the
        period (every IN trade of the stock when no holder is named).

    Contract:
        Input:
            (none)
        Output:
            instance; `build_items(labels, as_of)`, `build_buybacks(progs, before, items,
            restricted)`, `build_increases(items, trades, as_of, window_start)`; all pure
        Raises:
            (none at construction)

    Used by:
        portfolio.BuybackMonitorBuilder  -- both kinds' rows
        cli.ReportCommands               -- wires it

    Test cases:
        TC-BPF-001  build_items: one row per payload item, a label known after as_of is unseen
        TC-BPF-002  build_buybacks: 方案 + 报告书 labels join one programme, funding union and
                    loan kept; a later 预案 takes later labels; unlabelled restricted or
                    cap-less programmes are dropped; executed comes from the ledger, not summed
        TC-BPF-003  build_increases: repeat plans dropped; named holders only; avg_price else
                    close; trades after the period or after as_of are not counted; state open
                    / ended by the period end
    """

    def build_items(self, labels: pd.DataFrame, as_of: str) -> pd.DataFrame:
        """
        Purpose:
            One row per label item known on as_of.

        Contract:
            Input:
                labels: LabelStore rows of set buyback_terms (ts_code, doc_key, known_on,
                        payload); as_of: str (YYYYMMDD)
            Output:
                DataFrame  -- code, known_on, doc_key and _ITEM_FIELDS; sorted by known_on
            Raises:
                (none)
        """
        out: list[dict[str, Any]] = []
        for r in labels[labels["known_on"].astype(str) <= as_of].itertuples():
            for it in json.loads(str(r.payload)).get("items") or []:
                row = {"code": r.ts_code, "known_on": str(r.known_on), "doc_key": r.doc_key}
                out.append(row | {f: it.get(f) for f in _ITEM_FIELDS})
        cols = ["code", "known_on", "doc_key", *_ITEM_FIELDS]
        return pd.DataFrame(out, columns=cols).sort_values(["known_on", "doc_key"], kind="stable")

    def build_buybacks(
        self,
        progs: pd.DataFrame,
        before: pd.DataFrame,
        items: pd.DataFrame,
        restricted: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Purpose:
            The 回购 rows.

        Contract:
            Input:
                progs: BuybackLedger programmes on as_of; before: the same on the window start
                (for executed_before); items: build_items output; restricted: sec_code,
                ann_date of 限制性股票 titles
            Output:
                DataFrame  -- FRAME_COLUMNS, kind 回购, state open / stopped / expired
            Raises:
                (none)
        """
        p = progs[(progs["plan_date"].astype(str) >= START) & ~progs["seeded"].astype(bool)]
        p = p.sort_values(["ts_code", "plan_date", "programme"]).reset_index(drop=True)
        prior = before.set_index(["ts_code", "programme"])["executed_amount"]
        own = items[items["kind"] == "回购"]
        rs = {
            (str(c), str(d))
            for c, d in zip(restricted["sec_code"], restricted["ann_date"], strict=True)
        }
        out = []
        recs: list[dict[Any, Any]] = p.to_dict("records")
        for i, r in enumerate(recs):
            code, plan = str(r["ts_code"]), str(r["plan_date"])
            nxt = recs[i + 1] if i + 1 < len(recs) and recs[i + 1]["ts_code"] == code else None
            labs = self._find_labels(own, code, plan, nxt)
            if labs.empty and (self._is_restricted(rs, code, plan) or not r["high_limit"]):
                continue
            row = self._build_labels(labs, "purpose")
            row |= {
                "kind": "回购", "code": code, "date": plan, "end": str(r["exp_date"]),
                "state": r["state"], "executed": float(r["executed_amount"]),
                "executed_before": float(prior.get((code, r["programme"]), 0.0)),
                "labelled": not labs.empty,
            }  # fmt: skip
            if row["high"] is None:
                row["high"] = float(r["planned_amount"]) if r["planned_amount"] else None
            if row["price_cap"] is None and r["high_limit"]:
                row["price_cap"] = float(r["high_limit"])
            out.append(row)
        return pd.DataFrame(out, columns=FRAME_COLUMNS)

    def build_increases(
        self, items: pd.DataFrame, trades: pd.DataFrame, as_of: str, window_start: str
    ) -> pd.DataFrame:
        """
        Purpose:
            The 增持 rows.

        Contract:
            Input:
                items: build_items output; trades: IN rows of curated.stk_holdertrade
                (ts_code, ann_date, holder_name, change_vol, avg_price, close); as_of,
                window_start: str (YYYYMMDD)
            Output:
                DataFrame  -- FRAME_COLUMNS, kind 增持, state open / ended
            Raises:
                (none)
        """
        own = items[(items["kind"] == "增持") & (items["known_on"] >= START)].copy()
        keys = [
            (c, tuple(sorted(h or [])), *map(self._to_number, (lo, hi, sl, sh)))
            for c, h, lo, hi, sl, sh in zip(own["code"], own["holders"], own["amount_low"],
                                            own["amount_high"], own["shares_low"],
                                            own["shares_high"], strict=True)
        ]  # fmt: skip
        seen: set[tuple[Any, ...]] = set()
        first: list[bool] = []
        for k in keys:
            first.append(k not in seen)
            seen.add(k)
        own = own.loc[pd.Series(first, index=own.index, dtype=bool)]
        t = trades.assign(ann_date=trades["ann_date"].astype(str))
        t = t.assign(value=t["change_vol"] * t["avg_price"].fillna(t["close"]))
        out = []
        for r in own.to_dict("records"):
            code, start, holders = str(r["code"]), str(r["known_on"]), list(r["holders"] or [])
            period = r["period_months"]
            months = INCREASE_MONTHS if pd.isna(period) or not period else int(period)
            end = (pd.Timestamp(start) + pd.DateOffset(months=months)).strftime("%Y%m%d")
            row = self._build_labels(pd.DataFrame([r]), "holder_type")
            done = self._compute_trades(t, code, holders, start, min(end, as_of))
            prior = self._compute_trades(t, code, holders, start, min(end, window_start))
            row |= {
                "kind": "增持", "code": code, "date": start, "end": end,
                "state": "open" if end >= as_of else "ended", "executed": done,
                "executed_before": prior if window_start >= start else 0.0,
                "labelled": True,
            }  # fmt: skip
            out.append(row)
        return pd.DataFrame(out, columns=FRAME_COLUMNS)

    @staticmethod
    def _find_labels(own: pd.DataFrame, code: str, plan_date: str, nxt: Any) -> pd.DataFrame:
        d0 = pd.Timestamp(plan_date)
        lo = (d0 - pd.Timedelta(days=MATCH_DAYS)).strftime("%Y%m%d")
        hi = (d0 + pd.Timedelta(days=LABEL_DAYS)).strftime("%Y%m%d")
        if nxt is not None:
            stop = pd.Timestamp(nxt["plan_date"]) - pd.Timedelta(days=MATCH_DAYS + 1)
            hi = min(hi, stop.strftime("%Y%m%d"))
        m = (own["code"] == code) & (own["known_on"] >= lo) & (own["known_on"] <= hi)
        return own[m]

    @staticmethod
    def _is_restricted(rs: set[tuple[str, str]], code: str, plan_date: str) -> bool:
        d0 = pd.Timestamp(plan_date)
        days = range(-MATCH_DAYS, MATCH_DAYS + 1)
        return any((code[:6], (d0 + pd.Timedelta(days=k)).strftime("%Y%m%d")) in rs for k in days)

    @staticmethod
    def _build_labels(labs: pd.DataFrame, tag_field: str) -> dict[str, Any]:
        if labs.empty:
            return {"tags": [], "holders": [], "funding": [], "loan_bank": None,
                    "loan_amount": None, "low": None, "high": None, "price_cap": None}  # fmt: skip
        first = labs.iloc[0]
        funding: list[str] = []
        for f in labs["funding"]:
            funding += [x for x in (f or []) if x not in funding]
        banks = [b for b in labs["loan_bank"] if isinstance(b, str) and b]
        loans = [float(x) for x in labs["loan_amount"] if x is not None and not pd.isna(x)]
        return {
            "tags": list(first[tag_field] or []), "holders": list(first["holders"] or []),
            "funding": funding, "loan_bank": banks[0] if banks else None,
            "loan_amount": max(loans) if loans else None,
            "low": BuybackPlanFrame._to_number(first["amount_low"]),
            "high": BuybackPlanFrame._to_number(first["amount_high"]),
            "price_cap": BuybackPlanFrame._to_number(first["price_cap"]),
        }  # fmt: skip

    @staticmethod
    def _compute_trades(
        t: pd.DataFrame, code: str, holders: list[str], start: str, end: str
    ) -> float:
        m = (t["ts_code"] == code) & (t["ann_date"] >= start) & (t["ann_date"] <= end)
        rows = t[m]
        if holders:
            names = rows["holder_name"].astype(str)
            hit = [any(h in n or n in h for h in holders) for n in names]
            rows = rows.loc[pd.Series(hit, index=rows.index, dtype=bool)]
        return float(rows["value"].fillna(0.0).sum())

    @staticmethod
    def _to_number(v: Any) -> float | None:
        return None if v is None or pd.isna(v) else float(v)
