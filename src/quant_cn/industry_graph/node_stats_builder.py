"""Per-segment statistics of a period and the change between two periods (plan 28 ph3b-2)."""

from __future__ import annotations

import pandas as pd

STAT_COLUMNS = ["segment", "sector", "period", "n_companies", "sales", "top_companies"]
DIFF_COLUMNS = [
    "segment",
    "sector",
    "n_before",
    "n_after",
    "sales_before",
    "sales_after",
    "sales_change",
    "joined",
    "left",
]
UNMAPPED_COLUMNS = ["sector", "period", "item", "sales", "n_companies", "companies"]
TOP = 5  # companies listed per segment, and per unmapped item


class NodeStatsBuilder:
    """
    Purpose:
        Turn `node_member` rows into the material Opus curates taxonomy nodes from (plan 28
        ph3b-2, D-161):
        - `build_stats(members, period)`: per segment, the companies with revenue in it, their
          sales and the TOP companies by sales;
        - `build_diff(members, before, after)`: per segment, companies and sales in both periods,
          the sales change ratio, and the companies that joined or left;
        - `build_unmapped(members, period)`: revenue lines no node matched (how "none"), by the
          sector of the company's largest mapped segment (None when it has none), item, total
          sales and the companies reporting it, largest first.
        A company counts in a segment when it has a matched line there in that period.

    Contract:
        Input:
            (none)
        Output:
            instance; three methods returning DataFrames (STAT_COLUMNS, DIFF_COLUMNS,
            UNMAPPED_COLUMNS)
        Raises:
            (none)

    Used by:
        lake meta/runs/plan28_nodes.py (plan 28 phase 3b)

    Test cases:
        TC-NSB-001  build_stats counts companies and sums sales per segment; top companies
                    by sales
        TC-NSB-002  build_diff gives both periods, change ratio, joined and left companies;
                    a segment present in one period only is kept
        TC-NSB-003  build_unmapped groups unmatched lines by the company's main sector and
                    item; empty members give empty frames with their columns
    """

    def build_stats(self, members: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        Purpose:
            Per-segment statistics of one period.

        Contract:
            Input:
                members: DataFrame (node_member columns); period: str (YYYYMMDD)
            Output:
                DataFrame  -- STAT_COLUMNS, largest sales first
            Raises:
                (none)
        """
        rows = members[(members["period"] == period) & members["segment"].notna()]
        if rows.empty:
            return pd.DataFrame(columns=STAT_COLUMNS)
        out = []
        for (segment, sector), group in rows.groupby(["segment", "sector"], dropna=False):
            by_company = group.groupby("ts_code")["sales"].sum().sort_values(ascending=False)
            out.append({"segment": segment, "sector": sector, "period": period,
                        "n_companies": len(by_company), "sales": float(by_company.sum()),
                        "top_companies": ",".join(by_company.index[:TOP])})  # fmt: skip
        frame = pd.DataFrame(out, columns=STAT_COLUMNS)
        return frame.sort_values(["sales", "segment"], ascending=[False, True]).reset_index(
            drop=True
        )

    def build_diff(self, members: pd.DataFrame, before: str, after: str) -> pd.DataFrame:
        """
        Purpose:
            Per-segment change between two periods.

        Contract:
            Input:
                members: DataFrame; before, after: str (YYYYMMDD)
            Output:
                DataFrame  -- DIFF_COLUMNS, largest absolute sales change first
            Raises:
                (none)
        """
        rows = members[members["segment"].notna()]
        first = rows[rows["period"] == before].groupby("segment")
        last = rows[rows["period"] == after].groupby("segment")
        sector = rows.drop_duplicates("segment").set_index("segment")["sector"]
        segments = sorted({str(k) for k in first.groups} | {str(k) for k in last.groups})
        if not segments:
            return pd.DataFrame(columns=DIFF_COLUMNS)
        out = []
        for seg in segments:
            a = set(first.get_group(seg)["ts_code"]) if seg in first.groups else set()
            b = set(last.get_group(seg)["ts_code"]) if seg in last.groups else set()
            sa = float(first.get_group(seg)["sales"].sum()) if seg in first.groups else 0.0
            sb = float(last.get_group(seg)["sales"].sum()) if seg in last.groups else 0.0
            out.append({"segment": seg, "sector": sector.get(seg), "n_before": len(a),
                        "n_after": len(b), "sales_before": sa, "sales_after": sb,
                        "sales_change": (sb - sa) / sa if sa else None,
                        "joined": ",".join(sorted(b - a)),
                        "left": ",".join(sorted(a - b))})  # fmt: skip
        frame = pd.DataFrame(out, columns=DIFF_COLUMNS)
        frame["_abs"] = (frame["sales_after"] - frame["sales_before"]).abs()
        frame = frame.sort_values(["_abs", "segment"], ascending=[False, True])
        return frame.drop(columns="_abs").reset_index(drop=True)

    def build_unmapped(self, members: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        Purpose:
            Unmatched revenue lines of one period by sector and item.

        Contract:
            Input:
                members: DataFrame; period: str (YYYYMMDD)
            Output:
                DataFrame  -- UNMAPPED_COLUMNS, largest sales first
            Raises:
                (none)
        """
        rows = members[members["period"] == period]
        if rows.empty:
            return pd.DataFrame(columns=UNMAPPED_COLUMNS)
        mapped = rows[rows["sector"].notna()]
        main = mapped.sort_values("sales", ascending=False).drop_duplicates("ts_code")
        sector_of = main.set_index("ts_code")["sector"]
        lost = rows[rows["how"] == "none"].assign(sector=lambda f: f["ts_code"].map(sector_of))
        if lost.empty:
            return pd.DataFrame(columns=UNMAPPED_COLUMNS)
        out = []
        for (sector, item), group in lost.groupby(["sector", "item"], dropna=False):
            by_company = group.groupby("ts_code")["sales"].sum().sort_values(ascending=False)
            out.append({"sector": sector, "period": period, "item": item,
                        "sales": float(by_company.sum()), "n_companies": len(by_company),
                        "companies": ",".join(by_company.index[:TOP])})  # fmt: skip
        frame = pd.DataFrame(out, columns=UNMAPPED_COLUMNS)
        return frame.sort_values(["sales", "item"], ascending=[False, True]).reset_index(drop=True)
