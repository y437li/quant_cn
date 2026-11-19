"""财报季信号: per Shenwan L2 sector, does good news still lift the price? (plan 35, D-172)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_cn.calculation.earnings_event_builder import EarningsEventBuilder
from quant_cn.core.exceptions import LakeError
from quant_cn.core.sector_earnings_signal_settings import SectorEarningsSignalSettings
from quant_cn.lake.lake_query import LakeQuery

logger = logging.getLogger(__name__)

FILE_NAME = "sector_earnings_signal.json"
OPEN_END = "99991231"
STATUS_ORDER = {"firing": 0, "provisional": 1, "none": 2}
CURRENT_MIN_SHARE = 0.2  # the current season is the latest quarter with this share out overall
_MEMBERS = """
SELECT ts_code, l2_code, in_date, coalesce(out_date, '99991231') AS out_date
FROM curated.index_member_all WHERE l2_code IS NOT NULL
"""
_NAMES = """
SELECT index_code AS code, industry_name AS name FROM curated.index_classify
WHERE src = 'SW2021' AND level = 'L2'
"""
_INDEX = """
SELECT ts_code, trade_date, close FROM curated.sw_daily
WHERE trade_date <= ? AND ts_code IN (SELECT UNNEST(?))
"""
_HOLDERS = """
SELECT ts_code, end_date, arg_max(holder_num, ann_date) AS h FROM curated.stk_holdernumber
WHERE ann_date <= ? AND holder_num > 0 GROUP BY 1, 2
"""


class SectorEarningsSignalBuilder:
    """
    Purpose:
        The 财报季信号 document (plan 35, D-172). Earnings events (EarningsEventBuilder) are
        mapped to the Shenwan L2 sector they belonged to at the quarter end. Per sector and
        fiscal quarter:
        - n (events out by as_of with a SUE decile) and expected = max(n, the same count of
          the previous quarter); share = n / expected;
        - n_top, pre and react: count and mean pre / reaction excess (%) of the events in SUE
          deciles >= top_decile;
        - sig_date: the day 0 (first session on or after the disclosure) of the
          int(report_share x (expected - 1)) + 1-th event; before that the reading is
          provisional at as_of;
        - back: the sector-index excess (vs the mean L2 index) over back_window sessions
          before sig_date (or as_of); rally when back >= rally_min;
        - hchg: median change (%) of the members' shareholder counts at that quarter end.
        Status:
        - firing: share >= report_share, n_top >= min_events, pre >= pre_min and
          react <= react_max;
        - provisional: the same test before report_share;
        - none: otherwise.
        Firings carry fwd (sector excess fwd_windows sessions after sig_date; None until
        complete). The current season is the latest quarter with at least CURRENT_MIN_SHARE
        of its events out overall. new_flags lists sectors firing now that were not firing in
        the previous document. Nothing after as_of is read.

    Contract:
        Input:
            settings: SectorEarningsSignalSettings
            events:   EarningsEventBuilder
            query:    LakeQuery  -- curated index_member_all, index_classify, sw_daily,
                                    stk_holdernumber
        Output:
            instance; `build(previous, as_of) -> dict` (as_of, season, thresholds, rows: the
            current season per sector, firings first; history: the last history_quarters
            per sector; firings: every firing since start with fwd; record: mean fwd of past
            firings with and without a rally; new_flags), `write(out_dir, as_of)` -> Path
        Raises:
            (none at construction)

    Used by:
        cli.AppServiceBuilder  -- `build_sector_earnings_signal` (the CLI command writes)

    Test cases:
        TC-SEB-001  per sector and quarter: point-in-time membership, n / expected / share,
                    best-surprise pre and react means, sig_date at report_share
        TC-SEB-002  status firing / provisional / none at the thresholds; back and rally from
                    the sector index; fwd None until complete; new_flags only once
        TC-SEB-003  write puts sector_earnings_signal.json in the folder; a missing folder
                    raises LakeError; an empty lake gives a document without rows
    """

    def __init__(
        self,
        settings: SectorEarningsSignalSettings,
        events: EarningsEventBuilder,
        query: LakeQuery,
    ) -> None:
        self._s = settings
        self._events = events
        self._query = query

    def build(self, previous: dict[str, Any] | None, as_of: str) -> dict[str, Any]:
        """
        Purpose:
            The signal document as of a date.

        Contract:
            Input:
                previous: dict | None  -- last written document (for new_flags)
                as_of:    str YYYYMMDD
            Output:
                dict  -- see the class contract; rows / history / firings empty without data
            Raises:
                LakeError  -- a query fails
        """
        cells = self._build_cells(as_of)
        keys = ("pre_min", "react_max", "rally_min", "report_share", "top_decile", "min_events")
        doc: dict[str, Any] = {
            "as_of": as_of,
            "season": None,
            **{k: [] for k in ("rows", "history", "firings", "new_flags")},
            "record": {},
            "thresholds": {k: getattr(self._s, k) for k in keys},
        }
        if cells.empty:
            return doc
        season = self._get_season(cells)
        now = cells[cells["end_date"] == season].assign(
            rank=lambda f: f["status"].map(STATUS_ORDER)
        )
        now = now.sort_values(["rank", "pre"], ascending=[True, False], na_position="last")
        quarters = sorted(cells["end_date"].unique())[-self._s.history_quarters :]
        fired = cells[cells["status"] == "firing"].sort_values("sig_date")
        old = {r["code"] for r in (previous or {}).get("rows", []) if r.get("status") == "firing"}
        doc.update(
            season=season,
            rows=self._to_records(now),
            history=self._to_records(cells[cells["end_date"].isin(quarters)]),
            firings=self._to_records(fired),
            record=self._build_record(fired),
            new_flags=[c for c in now.loc[now["status"] == "firing", "code"] if c not in old],
        )
        return doc

    def write(self, out_dir: Path, as_of: str) -> Path:
        """
        Purpose:
            Build and write sector_earnings_signal.json into the app data folder.

        Contract:
            Input:
                out_dir: Path (existing folder); as_of: str YYYYMMDD
            Output:
                Path  -- the written file
            Raises:
                LakeError  -- out_dir missing or a query fails
        """
        if not out_dir.is_dir():
            raise LakeError(f"app data folder {out_dir} does not exist")
        path = out_dir / FILE_NAME
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        doc = self.build(previous, as_of)
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        logger.info("sector earnings signal: %d sectors in %s", len(doc["rows"]), doc["season"])
        return path

    def _build_cells(self, as_of: str) -> pd.DataFrame:
        ev = self._events.build(as_of)
        if ev.empty or not self._query.has_view("curated.index_member_all"):
            return pd.DataFrame()
        mem = self._query.sql(_MEMBERS)
        ev = ev.merge(mem, on="ts_code")
        ev = ev[(ev["in_date"] <= ev["end_date"]) & (ev["out_date"] > ev["end_date"])]
        ev = ev.drop_duplicates(["ts_code", "end_date"])
        cells = self._compute_summary(ev)
        cells = self._add_holders(cells, ev, as_of)
        names = (
            self._query.sql(_NAMES).set_index("code")["name"]
            if self._query.has_view("curated.index_classify")
            else pd.Series(dtype=str)
        )
        cells = self._add_index(cells, sorted(set(names.index) | set(cells["code"])), as_of)
        cells["status"] = self._get_status(cells)
        cells["name"] = cells["code"].map(names).fillna(cells["code"])
        return cells

    def _compute_summary(self, ev: pd.DataFrame) -> pd.DataFrame:
        s = self._s
        ev = ev[ev["dec"].notna()]  # events with a SUE and a pre window (the research basis)
        g = ev.groupby(["l2_code", "end_date"])
        cells = g.agg(n=("ts_code", "size")).reset_index().rename(columns={"l2_code": "code"})
        cells = cells.sort_values(["code", "end_date"])
        cells["expected"] = np.maximum(cells["n"], cells.groupby("code")["n"].shift().fillna(0))
        cells["share"] = cells["n"] / cells["expected"]
        need = (s.report_share * (cells["expected"] - 1)).astype(int) + 1
        days = (
            g["day0"].apply(lambda x: sorted(x.dropna().astype(str))).rename("days").reset_index()
        )
        cells = cells.merge(days.rename(columns={"l2_code": "code"}), on=["code", "end_date"])
        cells["sig_date"] = [
            d[k - 1] if len(d) >= k else None for d, k in zip(cells["days"], need, strict=True)
        ]
        top = (
            ev[ev["dec"] >= s.top_decile]
            .groupby(["l2_code", "end_date"])
            .agg(n_top=("ts_code", "size"), pre=("pre", "mean"), react=("react", "mean"))
        )
        top.index = top.index.set_names(["code", "end_date"])
        cells = cells.drop(columns="days").merge(
            top.reset_index(), on=["code", "end_date"], how="left"
        )
        cells["n_top"] = cells["n_top"].fillna(0).astype(int)
        return cells

    def _add_holders(self, cells: pd.DataFrame, ev: pd.DataFrame, as_of: str) -> pd.DataFrame:
        if not self._query.has_view("curated.stk_holdernumber"):
            return cells.assign(hchg=np.nan)
        h = self._query.sql(_HOLDERS, [as_of]).sort_values(["ts_code", "end_date"])
        h["hchg"] = h.groupby("ts_code")["h"].pct_change() * 100
        m = ev[["ts_code", "end_date", "l2_code"]].merge(h, on=["ts_code", "end_date"], how="left")
        med = m.groupby(["l2_code", "end_date"])["hchg"].median().rename_axis(["code", "end_date"])
        return cells.merge(med.reset_index(), on=["code", "end_date"], how="left")

    def _add_index(self, cells: pd.DataFrame, codes: list[str], as_of: str) -> pd.DataFrame:
        """Sector excess vs the mean of all L2 indices (`codes`) before and after each cell."""
        cells = cells.assign(back=np.nan, **{f"fwd{k}": np.nan for k in self._s.fwd_windows})
        if not self._query.has_view("curated.sw_daily"):
            return cells
        px = self._query.sql(_INDEX, [as_of, codes])
        if px.empty:
            return cells
        wide = px.pivot_table(index="trade_date", columns="ts_code", values="close").sort_index()
        wide.index = wide.index.astype(str)
        lr = pd.DataFrame(
            np.log(wide.to_numpy(dtype=float)), index=wide.index, columns=wide.columns
        ).diff()
        cum = lr.sub(lr.mean(axis=1), axis=0).fillna(0).cumsum() * 100
        dates = cum.index.to_numpy()
        signed = cells["sig_date"].notna().to_numpy()
        on = np.where(signed, cells["sig_date"].astype(str), as_of)
        at = np.searchsorted(dates, on, side="right") - 1  # last session on or before
        back = np.full(len(cells), np.nan)
        fwd = {w: np.full(len(cells), np.nan) for w in self._s.fwd_windows}
        for i, (code, k) in enumerate(zip(cells["code"], at, strict=True)):
            if code not in cum.columns or k < 0:
                continue
            col = cum[code].to_numpy()
            if k >= self._s.back_window:
                back[i] = col[k] - col[k - self._s.back_window]
            for w in self._s.fwd_windows:
                if signed[i] and k + w < len(col):
                    fwd[w][i] = col[k + w] - col[k]
        cells["back"] = back
        for w, vals in fwd.items():
            cells[f"fwd{w}"] = vals
        return cells

    def _get_status(self, cells: pd.DataFrame) -> pd.Series:
        s = self._s
        hit = (
            (cells["n_top"] >= s.min_events)
            & (cells["pre"] >= s.pre_min)
            & (cells["react"] <= s.react_max)
        )
        done = cells["share"] >= s.report_share
        return pd.Series(
            np.where(hit & done, "firing", np.where(hit, "provisional", "none")), index=cells.index
        )

    @staticmethod
    def _get_season(cells: pd.DataFrame) -> str:
        totals = cells.groupby("end_date")[["n", "expected"]].sum()
        live = totals[totals["n"] >= CURRENT_MIN_SHARE * totals["expected"]]
        return str((live if not live.empty else totals).index.max())

    def _build_record(self, fired: pd.DataFrame) -> dict[str, Any]:
        out: dict[str, Any] = {}
        rally = fired["back"] >= self._s.rally_min
        for label, part in (("rally", fired[rally]), ("all", fired)):
            out[label] = {
                f"fwd{w}": self._to_number(part[f"fwd{w}"].mean()) for w in self._s.fwd_windows
            }
            out[label]["n"] = int(part[f"fwd{self._s.fwd_windows[0]}"].notna().sum())
        return out

    def _to_records(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        cols = [
            "code",
            "name",
            "end_date",
            "status",
            "n",
            "expected",
            "share",
            "n_top",
            "pre",
            "react",
            "sig_date",
            "back",
            "hchg",
            *[f"fwd{w}" for w in self._s.fwd_windows],
        ]
        rows: list[dict[str, Any]] = []
        for rec in frame[cols].to_dict("records"):
            row: dict[str, Any] = {
                str(k): self._to_number(v) if isinstance(v, float) else v for k, v in rec.items()
            }
            row["rally"] = row["back"] is not None and row["back"] >= self._s.rally_min
            row["n"], row["expected"], row["n_top"] = (
                int(rec["n"]),
                int(rec["expected"]),
                int(rec["n_top"]),
            )
            row["sig_date"] = None if pd.isna(rec["sig_date"]) else str(rec["sig_date"])
            rows.append(row)
        return rows

    @staticmethod
    def _to_number(v: float) -> float | None:
        return None if v is None or pd.isna(v) else round(float(v), 2)
