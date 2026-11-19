"""Developers' monthly contracted sales and land payments from the 销售简报 (plan 31 ph4)."""

from __future__ import annotations

import json
import re

import pandas as pd

from quant_cn.lake.label_store import LabelStore
from quant_cn.portfolio.sector_metric_reader import LINE_COLUMNS, SectorMetricReader

TO_YI = {"亿元": 1.0, "万元": 1e-4, "元": 1e-8}
SALES = re.compile(r"(签约|合同销售|销售).*金额")
LAND = re.compile(r"价款|地价|土地款|土地.*金额")
MONTH = re.compile(r"^\d{4}-\d{2}$")
YTD = re.compile(r"^(\d{4})-01至\1-(\d{2})$")  # year-to-date period of a brief
ROLLING = 3  # months in the rolling sum of sales_yoy
STALE_MONTHS = 2  # YTD rows further behind the newest company's month are dropped
LAND_MONTHS = 12


class DeveloperSalesReader:
    """
    Purpose:
        Developers' figures from the operating_data label set (销售简报 read by
        OperatingDataExtractor, D-168), as LINE_COLUMNS lines:
        - `read_sales(names)`: monthly contracted sales (亿元; 万元 converted), single-month
          company totals only (items with a segment, e.g. a province breakdown, are skipped;
          of several totals in one brief the largest, i.e. total over equity), the latest
          filing per month;
        - `read_sales_yoy(names)`: year-on-year change (%) of the ROLLING-month sum of monthly
          sales; only windows whose months and prior-year months are all present (plan 33);
        - `read_ytd_yoy(names)`: year-to-date sales yoy (%) at each company's latest month,
          from the briefs' YTD totals (period "YYYY-01至YYYY-MM"), else from the monthly sum
          when every month of both years is present; a company whose latest month is more
          than STALE_MONTHS behind the latest month of all companies is left out;
        - `read_land_intensity(names)`: trailing LAND_MONTHS land payments / contracted sales
          (%). A brief's land payments (all parcels; of total and equity price the larger)
          count in the month the brief reports (the month before it was filed); only months
          with a full window of sales; a developer whose briefs report no land has no line.

    Contract:
        Input:
            labels: LabelStore; history_months: int > 0
        Output:
            instance; `read_sales`, `read_sales_yoy`, `read_ytd_yoy`, `read_land_intensity` ->
            DataFrame (LINE_COLUMNS)
        Raises:
            (none at construction)

    Used by:
        portfolio.SectorMonitorBuilder  -- contracted_sales and land_intensity charts
        cli.AppServiceBuilder  -- `build_sector_monitor`

    Test cases:
        TC-DEV-001  single-month 签约金额 items in 亿元 (万元 converted); a later filing of the
                    same month wins; year-to-date items are skipped
        TC-DEV-003  segment rows (per province) are skipped; of two totals in one brief the
                    larger is kept
        TC-DEV-004  rolling 3-month yoy needs all six months; YTD yoy from the printed YTD
                    totals, else from complete monthly sums; none when neither is available;
                    a company more than STALE_MONTHS behind is dropped
        TC-DEV-002  land intensity = 12-month land / 12-month sales in %; no label set gives
                    empty frames
    """

    def __init__(self, labels: LabelStore, history_months: int) -> None:
        self._labels = labels
        self._months = history_months

    def read_sales(self, names: dict[str, str]) -> pd.DataFrame:
        """
        Purpose:
            Monthly contracted sales per company from the 销售简报 items.

        Contract:
            Input:
                names: dict[str, str]  -- ts_code -> label
            Output:
                DataFrame  -- LINE_COLUMNS, period YYYY-MM, value 亿元
            Raises:
                (none)
        """
        return SectorMetricReader.get_recent(self._read_totals(names, MONTH), self._months)

    def read_sales_yoy(self, names: dict[str, str]) -> pd.DataFrame:
        """
        Purpose:
            Year-on-year change of the rolling ROLLING-month sales sum.

        Contract:
            Input:
                names: dict[str, str]  -- ts_code -> label
            Output:
                DataFrame  -- LINE_COLUMNS, period YYYY-MM (window end), value %
            Raises:
                (none)
        """
        rows = []
        for label, group in self._read_totals(names, MONTH).groupby("label"):
            by_month = {self._get_index(p): v for p, v in zip(group["period"], group["value"],
                                                              strict=True)}  # fmt: skip
            for end in sorted(by_month):
                now = self._get_window(by_month, end)
                then = self._get_window(by_month, end - 12)
                if now is not None and then:
                    rows.append({"label": label, "period": self._get_period(end),
                                 "value": (now / then - 1) * 100})  # fmt: skip
        out = pd.DataFrame(rows, columns=LINE_COLUMNS)
        return SectorMetricReader.get_recent(out, self._months)

    def read_ytd_yoy(self, names: dict[str, str]) -> pd.DataFrame:
        """
        Purpose:
            Year-to-date sales yoy at each company's latest reported month.

        Contract:
            Input:
                names: dict[str, str]  -- ts_code -> label
            Output:
                DataFrame  -- LINE_COLUMNS, one row per company with a value, period YYYY-MM
            Raises:
                (none)
        """
        monthly = self._read_totals(names, MONTH)
        ytd = self._read_totals(names, YTD)
        ytd["period"] = ytd["period"].str[-7:]  # "YYYY-01至YYYY-MM" -> "YYYY-MM"
        rows = []
        for label, group in monthly.groupby("label"):
            months = dict(zip(group["period"], group["value"], strict=True))
            printed = dict(zip(ytd.loc[ytd["label"] == label, "period"],
                               ytd.loc[ytd["label"] == label, "value"], strict=True))  # fmt: skip
            latest = max(months)
            now, then = (self._get_ytd(y, latest[5:], months, printed)
                         for y in (int(latest[:4]), int(latest[:4]) - 1))  # fmt: skip
            if now is not None and then:
                rows.append({"label": label, "period": latest, "value": (now / then - 1) * 100})
        out = pd.DataFrame(rows, columns=LINE_COLUMNS)
        if out.empty:
            return out
        newest = max(self._get_index(p) for p in out["period"])
        current = [newest - self._get_index(p) <= STALE_MONTHS for p in out["period"]]
        return out[current].reset_index(drop=True)

    def read_land_intensity(self, names: dict[str, str]) -> pd.DataFrame:
        """
        Purpose:
            Trailing 12-month land payments over contracted sales.

        Contract:
            Input:
                names: dict[str, str]  -- ts_code -> label
            Output:
                DataFrame  -- LINE_COLUMNS, period YYYY-MM (reported month), value %
            Raises:
                (none)
        """
        sales = self.read_sales(names)
        items = self._read_items(names, LAND, latest_only=False)
        if sales.empty or items.empty:
            return pd.DataFrame(columns=LINE_COLUMNS)
        # every parcel of a brief counts; total and equity price of the same parcels are two
        # metrics, so per brief the larger metric total is kept
        per_metric = items.groupby(["label", "known_on", "metric"], as_index=False)["value"].sum()
        land = pd.DataFrame(
            per_metric.groupby(["label", "known_on"], as_index=False)["value"].max()
        )
        land["period"] = land["known_on"].map(self._get_reported_month)
        land = pd.DataFrame(land.groupby(["label", "period"], as_index=False)["value"].sum())
        out = []
        for label, group in sales.groupby("label"):
            spend = land[land["label"] == label].set_index("period")["value"]
            if spend.sum() <= 0:
                continue  # a developer whose briefs report no land purchases has no line
            monthly = pd.DataFrame({"sales": group.set_index("period")["value"]})
            monthly = monthly.join(spend.rename("land"), how="left").fillna({"land": 0.0})
            monthly = monthly.sort_index()
            rolled = monthly.rolling(LAND_MONTHS, min_periods=LAND_MONTHS).sum()
            ratio = (rolled["land"] / rolled["sales"] * 100).dropna().round(1)
            out += [{"label": label, "period": p, "value": v} for p, v in ratio.items()]
        return pd.DataFrame(out, columns=LINE_COLUMNS)

    def _read_items(
        self,
        names: dict[str, str],
        pattern: re.Pattern[str],
        latest_only: bool = True,
        totals_only: bool = False,
    ) -> pd.DataFrame:
        cols = [*LINE_COLUMNS, "known_on", "metric"]
        if "operating_data" not in self._labels.list_sets():
            return pd.DataFrame(columns=cols)
        filed = self._labels.read("operating_data")
        filed = filed[filed["ts_code"].isin(list(names))]
        rows = []
        for ts, known, payload in filed[["ts_code", "known_on", "payload"]].itertuples(False):
            for item in json.loads(payload).get("items", []):
                scale = TO_YI.get(str(item.get("unit")))
                value, period = item.get("value"), str(item.get("period") or "")
                if scale is None or not isinstance(value, int | float) or not period:
                    continue
                if totals_only and item.get("segment"):
                    continue
                if pattern.search(str(item.get("metric") or "")):
                    rows.append({"label": names[ts], "period": period,
                                 "value": float(value) * scale, "known_on": known,
                                 "metric": str(item.get("metric"))})  # fmt: skip
        frame = pd.DataFrame(rows, columns=cols).sort_values("known_on")
        if latest_only:
            frame = frame.drop_duplicates(["label", "period"], keep="last")
        return frame.reset_index(drop=True)

    def _read_totals(self, names: dict[str, str], period: re.Pattern[str]) -> pd.DataFrame:
        """Company-total sales per (label, period) whose period matches; largest per brief, latest
        filing per period."""
        items = self._read_items(names, SALES, latest_only=False, totals_only=True)
        items = items[items["period"].str.match(period.pattern)]
        per_brief = pd.DataFrame(
            items.groupby(["label", "period", "known_on"], as_index=False)["value"].max()
        )
        latest = per_brief.sort_values("known_on").drop_duplicates(["label", "period"], keep="last")
        return pd.DataFrame(latest[LINE_COLUMNS]).reset_index(drop=True)

    @staticmethod
    def _get_ytd(
        year: int, month: str, months: dict[str, float], printed: dict[str, float]
    ) -> float | None:
        """YTD sales to `month` of `year`: the printed total, else a complete monthly sum."""
        end = f"{year}-{month}"
        if end in printed:
            return printed[end]
        values = [months.get(f"{year}-{m:02d}") for m in range(1, int(month) + 1)]
        return None if None in values else float(sum(v for v in values if v is not None))

    @staticmethod
    def _get_window(by_month: dict[int, float], end: int) -> float | None:
        """Sum of the ROLLING months ending at month index `end`; None if one is missing."""
        values = [by_month.get(end - k) for k in range(ROLLING)]
        return None if None in values else float(sum(v for v in values if v is not None))

    @staticmethod
    def _get_index(period: str) -> int:
        """Months since year 0 of a YYYY-MM period."""
        return int(period[:4]) * 12 + int(period[5:7]) - 1

    @staticmethod
    def _get_period(index: int) -> str:
        return f"{index // 12}-{index % 12 + 1:02d}"

    @staticmethod
    def _get_reported_month(known_on: str) -> str:
        """The month a brief filed on `known_on` (YYYYMMDD) reports: the one before."""
        year, month = int(known_on[:4]), int(known_on[4:6]) - 1
        return f"{year - 1}-12" if month == 0 else f"{year}-{month:02d}"
