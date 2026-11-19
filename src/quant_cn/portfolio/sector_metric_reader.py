"""Lake reads behind the sector monitor's charts (plan 31 ph4)."""

from __future__ import annotations

import pandas as pd

from quant_cn.core.sector_monitor_settings import SectorMonitorSettings
from quant_cn.lake.graph_store import GraphStore
from quant_cn.lake.lake_query import LakeQuery

LINE_COLUMNS = ["label", "period", "value"]
YI = 1e8  # 亿元
OTHER_TIER = "三线"
BREADTH_LABELS = {"new": "新房", "second_hand": "二手"}
_QUARTERLY = """
    SELECT ts_code, end_date, arg_max({col}, ann_date) AS v FROM curated.{table}
    WHERE report_type = '1' AND ts_code IN (SELECT UNNEST(?)) AND end_date >= ?
    GROUP BY 1, 2"""


class SectorMetricReader:
    """
    Purpose:
        Read each sector-monitor metric (plan 31 ph4, D-168) as long lines (LINE_COLUMNS:
        label = company name, tier or "全部", period, value):
        - `read_house_prices(kind)`: 70-city month-on-month change (index - 100, %) averaged
          per tier (settings.tiers; other cities form 三线), period YYYY-MM;
        - `read_house_breadth()`: cities with a month-on-month fall (index < 100) per month,
          lines 新房 and 二手 (plan 33, D-170);
        - `read_quarterly(names, metric)`: contract_liab (亿元, balance), impairment (asset +
          credit impairment, single quarter, positive = a charge, 亿元), revenue_q (single
          quarter revenue, 亿元), selling_ratio (single quarter sell_exp / revenue, %); first
          filed statements (report_type 1), latest announcement per period;
        - `read_dividends(names)`: cash dividend per share (pre-tax) by fiscal year, summing
          interim and final payouts; plans that failed or stopped, and zero rows, are skipped;
        - `read_winner_rate(names)`: daily cyq_perf winner_rate (%);
        - `read_closes(codes, index_code)`: wide adjusted closes of the companies and the
          Shenwan index close, for realised vol;
        - `read_game_approvals(names)`: approvals per month (list publication month): 全部 and
          each company (game_company, distinct approvals).
        Missing views or tables give empty frames.

    Contract:
        Input:
            settings: SectorMonitorSettings; query: LakeQuery; graph: GraphStore
        Output:
            instance; the read_* methods above; every frame LINE_COLUMNS except read_closes
            (index trade_date, one column per code)
        Raises:
            (none at construction)

    Used by:
        portfolio.DeveloperSalesReader  -- get_recent
        portfolio.MarketSignalReader  -- get_recent, LINE_COLUMNS
        portfolio.SectorMonitorBuilder  -- every chart line
        cli.AppServiceBuilder  -- `build_sector_monitor`

    Test cases:
        TC-SMR-001  tier averages of mom - 100 per month; cities outside the lists are 三线
        TC-SMR-002  dividends per fiscal year; winner rate and closes (company adjusted
                    closes plus the Shenwan index); missing views give empty frames
        TC-SMR-004  breadth counts cities below 100 per month and house type
        TC-SMR-003  impairment: single quarter from year-to-date, sign flipped; selling ratio
                    in %; game approvals per month for 全部 and per company
    """

    def __init__(
        self,
        settings: SectorMonitorSettings,
        query: LakeQuery,
        graph: GraphStore,
    ) -> None:
        self._s = settings
        self._query = query
        self._graph = graph

    def read_house_prices(self, kind: str) -> pd.DataFrame:
        """
        Purpose:
            Tier averages of the 70-city month-on-month change.

        Contract:
            Input:
                kind: str  -- "new" | "second_hand"
            Output:
                DataFrame  -- LINE_COLUMNS, period YYYY-MM, value in %
            Raises:
                (none)
        """
        if not self._query.has_view("curated.house_price_70"):
            return pd.DataFrame(columns=LINE_COLUMNS)
        frame = self._query.sql(
            "SELECT month, city, mom FROM curated.house_price_70 WHERE house_type = ?", [kind]
        )
        tier_of = {city: tier for tier, cities in self._s.tiers.items() for city in cities}
        frame["label"] = frame["city"].map(tier_of).fillna(OTHER_TIER)
        frame["period"] = frame["month"].str[:4] + "-" + frame["month"].str[4:]
        out = pd.DataFrame(frame.groupby(["label", "period"], as_index=False)["mom"].mean())
        out["value"] = (out["mom"] - 100).round(3)
        return self.get_recent(out[LINE_COLUMNS], self._s.history_months)

    def read_house_breadth(self) -> pd.DataFrame:
        """
        Purpose:
            Number of the 70 cities whose month-on-month index is below 100.

        Contract:
            Input:
                (none)
            Output:
                DataFrame  -- LINE_COLUMNS, label 新房 | 二手, period YYYY-MM, value cities
            Raises:
                (none)
        """
        if not self._query.has_view("curated.house_price_70"):
            return pd.DataFrame(columns=LINE_COLUMNS)
        frame = self._query.sql(
            "SELECT house_type, month, count_if(mom < 100) AS value FROM curated.house_price_70 "
            "GROUP BY 1, 2"
        )
        frame["label"] = frame["house_type"].map(BREADTH_LABELS)
        frame["period"] = frame["month"].str[:4] + "-" + frame["month"].str[4:]
        frame["value"] = frame["value"].astype(float)
        return self.get_recent(frame.dropna(subset=["label"])[LINE_COLUMNS], self._s.history_months)

    def read_quarterly(self, names: dict[str, str], metric: str) -> pd.DataFrame:
        """
        Purpose:
            One quarterly statement metric per company.

        Contract:
            Input:
                names: dict[str, str]; metric: str  -- contract_liab | impairment |
                revenue_q | selling_ratio
            Output:
                DataFrame  -- LINE_COLUMNS, period = end_date YYYYMMDD
            Raises:
                (none)
        """
        start = self._get_start()
        if metric == "contract_liab":
            frame = self._read_statement(names, "balancesheet_vip", "contract_liab", start)
            frame["value"] = frame["v"] / YI
        elif metric == "impairment":
            a = self._read_single(names, "assets_impair_loss", start)
            c = self._read_single(names, "credit_impa_loss", start)
            frame = a.merge(c, on=["ts_code", "end_date"], how="outer", suffixes=("_a", "_c"))
            frame["value"] = -(frame["v_a"].fillna(0) + frame["v_c"].fillna(0)) / YI
        else:
            frame = self._read_single(names, "revenue", start)
            if metric == "selling_ratio":
                sell = self._read_single(names, "sell_exp", start)
                frame = frame.merge(sell, on=["ts_code", "end_date"], suffixes=("_r", "_s"))
                frame["value"] = frame["v_s"] / frame["v_r"] * 100
            else:
                frame["value"] = frame["v"] / YI
        frame["label"] = frame["ts_code"].map(names)
        frame["period"] = frame["end_date"]
        frame["value"] = frame["value"].round(2)
        return self.get_recent(frame[LINE_COLUMNS].dropna(), self._s.history_quarters)

    def read_dividends(self, names: dict[str, str]) -> pd.DataFrame:
        """
        Purpose:
            Cash dividend per share (pre-tax) by fiscal year.

        Contract:
            Input:
                names: dict[str, str]
            Output:
                DataFrame  -- LINE_COLUMNS, period YYYY, value 元 / share
            Raises:
                (none)
        """
        if not self._query.has_view("curated.dividend"):
            return pd.DataFrame(columns=LINE_COLUMNS)
        frame = self._query.sql(
            "SELECT ts_code, substr(end_date, 1, 4) AS period, arg_max(cash_div_tax, ann_date) "
            "AS value FROM curated.dividend WHERE ts_code IN (SELECT UNNEST(?)) "
            "AND cash_div_tax > 0 AND div_proc NOT LIKE '%未通过%' AND div_proc NOT LIKE '%停止%' "
            "GROUP BY 1, 2",
            [list(names)],
        )
        frame["label"] = frame["ts_code"].map(names)
        summed = pd.DataFrame(frame.groupby(["label", "period"], as_index=False)["value"].sum())
        return self.get_recent(summed[LINE_COLUMNS], 6)

    def read_winner_rate(self, names: dict[str, str]) -> pd.DataFrame:
        """
        Purpose:
            Daily share of chips in profit (获利盘).

        Contract:
            Input:
                names: dict[str, str]
            Output:
                DataFrame  -- LINE_COLUMNS, period YYYYMMDD, value %
            Raises:
                (none)
        """
        if not self._query.has_view("curated.cyq_perf"):
            return pd.DataFrame(columns=LINE_COLUMNS)
        frame = self._query.sql(
            "SELECT ts_code, trade_date AS period, winner_rate AS value FROM curated.cyq_perf "
            "WHERE ts_code IN (SELECT UNNEST(?))",
            [list(names)],
        )
        frame["label"] = frame["ts_code"].map(names)
        return self.get_recent(frame[LINE_COLUMNS], self._s.history_sessions)

    def read_closes(self, codes: list[str], index_code: str) -> pd.DataFrame:
        """
        Purpose:
            Wide closes for realised vol: adjusted company closes and the index close.

        Contract:
            Input:
                codes: list[str]; index_code: str (Shenwan, curated.sw_daily)
            Output:
                DataFrame  -- index trade_date ascending, one column per code
            Raises:
                (none)
        """
        frames = []
        if self._query.has_view("derived.prices_adj"):
            frames.append(self._query.sql(
                "SELECT ts_code, trade_date, close_adj AS close FROM derived.prices_adj "
                "WHERE ts_code IN (SELECT UNNEST(?))", [codes]))  # fmt: skip
        if self._query.has_view("curated.sw_daily"):
            frames.append(self._query.sql(
                "SELECT ts_code, trade_date, close FROM curated.sw_daily WHERE ts_code = ?",
                [index_code]))  # fmt: skip
        if not frames:
            return pd.DataFrame()
        long = pd.concat(frames, ignore_index=True)
        wide = long.pivot_table(index="trade_date", columns="ts_code", values="close")
        wide.index = wide.index.astype(str)
        return wide.sort_index()

    def read_game_approvals(self, names: dict[str, str]) -> pd.DataFrame:
        """
        Purpose:
            Game approvals per month: all approvals and each company's.

        Contract:
            Input:
                names: dict[str, str]
            Output:
                DataFrame  -- LINE_COLUMNS, period YYYY-MM (list publication), value count
            Raises:
                (none)
        """
        if "game_company" not in self._graph.list_tables():
            return pd.DataFrame(columns=LINE_COLUMNS)
        links = self._graph.read("game_company")
        links["period"] = links["known_on"].str[:4] + "-" + links["known_on"].str[4:6]
        total = links.groupby("period")["approval_no"].nunique().rename("value").reset_index()
        total["label"] = "全部"
        own = links[links["ts_code"].isin(list(names))].assign(
            label=lambda f: f["ts_code"].map(names)
        )
        per = own.groupby(["label", "period"])["approval_no"].nunique().rename("value")
        out = pd.concat([total, per.reset_index()], ignore_index=True)
        return self.get_recent(out[LINE_COLUMNS], self._s.history_months)

    def _get_start(self) -> str:
        """January 1 of the year that covers history_quarters before the latest statement."""
        if not self._query.has_view("curated.income_vip"):
            return "00000000"
        latest = str(self._query.sql("SELECT max(end_date) AS m FROM curated.income_vip")["m"][0])
        years = self._s.history_quarters // 4 + 1
        return f"{int(latest[:4]) - years}0101"

    def _read_statement(
        self, names: dict[str, str], table: str, col: str, start: str
    ) -> pd.DataFrame:
        if not self._query.has_view(f"curated.{table}"):
            return pd.DataFrame(columns=["ts_code", "end_date", "v"])
        return self._query.sql(_QUARTERLY.format(col=col, table=table), [list(names), start])

    def _read_single(self, names: dict[str, str], col: str, start: str) -> pd.DataFrame:
        """Single-quarter values of a year-to-date income column (missing quarters as 0)."""
        frame = self._read_statement(names, "income_vip", col, start)
        frame = frame.sort_values(["ts_code", "end_date"]).assign(v=lambda f: f["v"].fillna(0.0))
        year = frame["end_date"].str[:4]
        frame["v"] = frame["v"] - frame.groupby([frame["ts_code"], year])["v"].shift().fillna(0.0)
        return frame

    @staticmethod
    def get_recent(frame: pd.DataFrame, periods: int) -> pd.DataFrame:
        """
        Purpose:
            The rows of the last `periods` distinct periods, sorted by label and period.

        Contract:
            Input:
                frame: DataFrame (LINE_COLUMNS); periods: int > 0
            Output:
                DataFrame
            Raises:
                (none)
        """
        keep = sorted(frame["period"].unique())[-periods:]
        out = frame[frame["period"].isin(keep)].sort_values(["label", "period"])
        return out.reset_index(drop=True)
