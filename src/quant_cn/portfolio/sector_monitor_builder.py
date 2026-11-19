"""The sector monitor document (#sector-monitor, plan 31 ph4)."""

from __future__ import annotations

import json
import logging
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from quant_cn.calculation.realized_vol_calculator import RealizedVolCalculator
from quant_cn.core.exceptions import LakeError
from quant_cn.core.sector_monitor_settings import MonitoredSector, SectorMonitorSettings
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.portfolio.app_rank_reader import AppRankReader
from quant_cn.portfolio.developer_sales_reader import DeveloperSalesReader
from quant_cn.portfolio.market_signal_reader import MarketSignalReader
from quant_cn.portfolio.sector_metric_reader import LINE_COLUMNS, SectorMetricReader

logger = logging.getLogger(__name__)
FILE_NAME = "sector_monitor.json"
TITLES = {  # metric -> (chart title, unit)
    "house_price_second_hand": ("70 城二手住宅价格环比", "%"),
    "house_price_new": ("70 城新建住宅价格环比", "%"),
    "contracted_sales": ("月度签约销售额", "亿元"),
    "land_intensity": ("拿地强度(12 个月拿地 / 签约)", "%"),
    "contract_liab": ("合同负债", "亿元"),
    "impairment": ("单季资产 + 信用减值", "亿元"),
    "dividend": ("每股现金分红(税前)", "元"),
    "winner_rate": ("获利盘", "%"),
    "realized_vol": ("20 日实际波动率(年化)", "%"),
    "game_approvals": ("每月版号数", "款"),
    "revenue_q": ("单季营收", "亿元"),
    "selling_ratio": ("单季销售费用率", "%"),
    "app_rank": ("畅销榜最佳排名(App Store)", "名"),
    "sales_yoy": ("签约额同比(滚动 3 个月)", "%"),
    "house_price_breadth": ("70 城环比下跌城市数", "城"),
    "valuation": ("{field} 5 年分位", "%"),
    "revision": ("盈利预测修正(3 个月)", "%"),
    "surveys": ("机构调研(天 / 月)", "次"),
}
FIELD_NAMES = {"pb": "PB", "pe_ttm": "PE(TTM)"}
# metric -> (table key, column label, unit) of an extra table value read with the chart (plan 33)
EXTRAS = {"sales_yoy": ("sales_yoy_ytd", "累计同比", "%"), "valuation": ("valuation_level", "", ""),
          "surveys": ("surveys_recent", "近 90 天调研", "次")}  # fmt: skip
NOT_IN_TABLE = ("sales_yoy", "surveys")  # the extra value is the table column instead
DATED = ("valuation", "revision", "surveys")  # need the sector as_of
STALE = 2  # a company's last point must be among the chart's last STALE periods (ranks: 1)
QUARTERLY = ("contract_liab", "impairment", "revenue_q", "selling_ratio")
DAILY = ("winner_rate", "valuation")  # charted weekly, like realised vol
WEEK = 5  # sessions between chart points of daily series
RANKED = ("app_rank",)  # lower is better: the chart axis is drawn inverted


class SectorMonitorBuilder:
    """
    Purpose:
        Build `sector_monitor.json` for the #sector-monitor tab (plan 31 ph4, D-168): per
        configured sector one chart per metric (TITLES; lines of LINE_COLUMNS turned into
        points [period, value]) and a company table with the latest value of each line plus
        realised vol (each `vol_windows` window, %, with the 20-day vol's trailing percentile)
        and the RetailGauge reading (ChipStructureReader); the table's first row is the
        Shenwan index (kind "index", vol only). The realised-vol chart has the
        Shenwan index and every company over `history_sessions` sessions; daily charts
        (realised vol, 获利盘) keep every WEEK-th session counted back from the latest (the
        table keeps the daily latest). `as_of` is the last
        session with an index close. A sector with the app_rank metric also gets `rankings`
        (AppRankReader.read_rankings: its games on the App Store charts and the home top list);
        rank charts carry `invert: true`, and a company off the chart at the latest capture
        has no rank in the table. Plan 33 (D-170) adds sales_yoy, house_price_breadth,
        valuation (percentile chart, level as an extra column), revision and surveys
        (MarketSignalReader); a chart carries `in_table` and its `extra` column (EXTRAS); a
        company whose last point is older than the chart's last STALE periods has no table
        value.

    Contract:
        Input:
            settings: SectorMonitorSettings; metrics: SectorMetricReader;
            sales: DeveloperSalesReader; vols: RealizedVolCalculator; chips: ChipStructureReader;
            apps: AppRankReader; signals: MarketSignalReader
        Output:
            instance; `build() -> dict`; `write(out_dir) -> Path`
        Raises:
            (none at construction)

    Used by:
        cli.AppServiceBuilder  -- `build_sector_monitor`

    Test cases:
        TC-SMB-001  a sector gives one chart per metric with its lines and a table row per
                    company (latest values, vol, vol percentile, retail_gauge)
        TC-SMB-002  the realised-vol chart has the index and companies; NaN values are
                    dropped from points; a metric without data gives an empty chart
        TC-SMB-004  app_rank: an inverted chart, the latest rank in the table and the
                    rankings block; a company off the chart at the latest capture has no rank;
                    sectors without app_rank have no rankings
        TC-SMB-005  plan 33 metrics: extra columns (YTD yoy, valuation level, recent surveys),
                    in_table flags, a stale company point left out of the table
        TC-SMB-003  write puts sector_monitor.json in the directory; a missing one raises
                    LakeError
    """

    def __init__(
        self,
        settings: SectorMonitorSettings,
        metrics: SectorMetricReader,
        sales: DeveloperSalesReader,
        vols: RealizedVolCalculator,
        chips: ChipStructureReader,
        apps: AppRankReader,
        signals: MarketSignalReader,
    ) -> None:
        self._s = settings
        self._metrics = metrics
        self._sales = sales
        self._vols = vols
        self._chips = chips
        self._apps = apps
        self._signals = signals

    def build(self) -> dict[str, Any]:
        """
        Purpose:
            The whole document.

        Contract:
            Input:
                (none)
            Output:
                dict  -- {"as_of", "sectors": [{"key", "name", "index", "charts", "table",
                "rankings" (app_rank sectors only)}]}
            Raises:
                LakeError  -- a lake query fails
        """
        sectors = [self._build_sector(sector) for sector in self._s.sectors]
        as_of = max((s["as_of"] for s in sectors if s["as_of"]), default=None)
        return {"as_of": as_of, "sectors": sectors}

    def write(self, out_dir: Path) -> Path:
        """
        Purpose:
            Build and write sector_monitor.json into `out_dir`.

        Contract:
            Input:
                out_dir: Path  -- existing directory
            Output:
                Path  -- the written file
            Raises:
                LakeError  -- `out_dir` missing, or the build fails
        """
        if not out_dir.is_dir():
            raise LakeError(f"output directory does not exist: {out_dir}")
        doc = self.build()
        path = out_dir / FILE_NAME
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("sector monitor: %d sectors as of %s -> %s", len(doc["sectors"]),
                    doc["as_of"], path)  # fmt: skip
        return path

    def _build_sector(self, sector: MonitoredSector) -> dict[str, Any]:
        names = {c.code: c.name for c in sector.companies}
        charts: list[dict[str, Any]] = []
        latest: dict[str, dict[str, Any]] = {n: {} for n in [sector.index.name, *names.values()]}
        closes = self._metrics.read_closes(list(names), sector.index.code)
        as_of = str(closes.index[-1]) if not closes.empty else None
        for metric in sector.metrics:
            if metric == "realized_vol":
                lines, extra = self._build_vol_lines(closes, names, sector, latest), None
            else:
                lines, extra = self._read_lines(metric, names, sector, as_of)
                if metric in DAILY and not lines.empty:
                    lines = self._build_weekly_lines(lines)
                self._record_latest(metric, lines, extra, latest)
            charts.append(self._build_chart(metric, sector, lines, extra))
        gauge = self._chips.read(list(names), as_of)["retail_gauge"] if as_of else None
        table = [{"code": sector.index.code, "name": sector.index.name, "kind": "index",
                  **latest[sector.index.name]}]  # fmt: skip
        for code, name in names.items():
            row = {"code": code, "name": name, "kind": "company", **latest[name]}
            row["retail_gauge"] = self._get_number(gauge[code]) if gauge is not None else None
            table.append(row)
        doc = {"key": sector.key, "name": sector.name, "as_of": as_of,
               "index": {"code": sector.index.code, "name": sector.index.name},
               "charts": charts, "table": table}  # fmt: skip
        if "app_rank" in sector.metrics:
            doc["rankings"] = self._apps.read_rankings(names)
        return doc

    def _read_lines(
        self, metric: str, names: dict[str, str], sector: MonitoredSector, as_of: str | None
    ) -> tuple[pd.DataFrame, pd.DataFrame | None]:
        """The chart lines of a metric and, for EXTRAS metrics, the extra table values."""
        if metric in QUARTERLY:
            return self._metrics.read_quarterly(names, metric), None
        if metric in DATED:
            if as_of is None:
                return pd.DataFrame(columns=LINE_COLUMNS), None
            index = (sector.index.code, sector.index.name)
            dated: dict[str, Callable[[], tuple[pd.DataFrame, pd.DataFrame | None]]] = {
                "valuation": lambda: self._signals.read_valuation(
                    names, index, sector.valuation, as_of
                ),
                "revision": lambda: (self._signals.read_revisions(names, as_of), None),
                "surveys": lambda: self._signals.read_surveys(names, as_of),
            }
            return dated[metric]()
        if metric == "sales_yoy":
            return self._sales.read_sales_yoy(names), self._sales.read_ytd_yoy(names)
        readers: dict[str, Callable[[], pd.DataFrame]] = {
            "house_price_second_hand": lambda: self._metrics.read_house_prices("second_hand"),
            "house_price_new": lambda: self._metrics.read_house_prices("new"),
            "house_price_breadth": self._metrics.read_house_breadth,
            "contracted_sales": lambda: self._sales.read_sales(names),
            "land_intensity": lambda: self._sales.read_land_intensity(names),
            "dividend": lambda: self._metrics.read_dividends(names),
            "winner_rate": lambda: self._metrics.read_winner_rate(names),
            "game_approvals": lambda: self._metrics.read_game_approvals(names),
            "app_rank": lambda: self._apps.read_rank_lines(names),
        }
        return readers[metric](), None

    def _record_latest(
        self,
        metric: str,
        lines: pd.DataFrame,
        extra: pd.DataFrame | None,
        latest: dict[str, dict[str, Any]],
    ) -> None:
        """Latest value per label (current points only) and the extra column into `latest`."""
        keep = 1 if metric in RANKED else STALE
        recent = set(sorted(lines["period"].unique())[-keep:]) if not lines.empty else set()
        for label, group in lines.groupby("label"):
            if label in latest and group["period"].iloc[-1] in recent:
                latest[str(label)][metric] = self._get_number(group["value"].iloc[-1])
        if extra is not None and metric in EXTRAS:
            for label, value in zip(extra["label"], extra["value"], strict=True):
                if label in latest:
                    latest[str(label)][EXTRAS[metric][0]] = self._get_number(value)

    def _build_chart(
        self,
        metric: str,
        sector: MonitoredSector,
        lines: pd.DataFrame,
        extra: pd.DataFrame | None,
    ) -> dict[str, Any]:
        title, unit = TITLES[metric]
        field = FIELD_NAMES[sector.valuation]
        chart: dict[str, Any] = {
            "key": metric, "title": title.format(field=field), "unit": unit,
            "invert": metric in RANKED, "in_table": metric not in NOT_IN_TABLE,
            "lines": self._build_points(lines),
        }  # fmt: skip
        if metric in EXTRAS and extra is not None:
            key, label, extra_unit = EXTRAS[metric]
            chart["extra"] = {"key": key, "label": label or field, "unit": extra_unit}
        return chart

    def _build_vol_lines(
        self,
        closes: pd.DataFrame,
        names: dict[str, str],
        sector: MonitoredSector,
        latest: dict[str, dict[str, Any]],
    ) -> pd.DataFrame:
        if closes.empty:
            return pd.DataFrame(columns=LINE_COLUMNS)
        labels = {**names, sector.index.code: sector.index.name}
        rows = []
        for window in self._s.vol_windows:
            vol = self._vols.compute_vol(closes, window)
            for code in vol.columns:
                series = vol[code].dropna()
                if series.empty or code not in labels:
                    continue
                label = labels[str(code)]
                latest[label][f"vol_{window}"] = self._get_number(series.iloc[-1])
                pct = self._vols.compute_rank_pct(vol[code]).dropna()
                if not pct.empty:
                    latest[label][f"vol_{window}_pct"] = self._get_number(pct.iloc[-1])
            if window == self._s.vol_windows[0]:
                tail = self._build_weekly(vol.tail(self._s.history_sessions))
                for code in tail.columns:
                    label = labels.get(str(code), str(code))
                    rows += [{"label": label, "period": day, "value": v}
                             for day, v in tail[code].dropna().items()]  # fmt: skip
        return pd.DataFrame(rows, columns=LINE_COLUMNS)

    @classmethod
    def _build_weekly_lines(cls, lines: pd.DataFrame) -> pd.DataFrame:
        """Weekly points of daily lines (LINE_COLUMNS), the latest kept."""
        wide = lines.pivot_table(index="period", columns="label", values="value").sort_index()
        sampled = cls._build_weekly(wide)
        long = sampled.reset_index().melt(id_vars="period", var_name="label", value_name="value")
        return (
            long.dropna(subset=["value"])[LINE_COLUMNS]
            .sort_values(["label", "period"])
            .reset_index(drop=True)
        )

    @staticmethod
    def _build_weekly(frame: pd.DataFrame) -> pd.DataFrame:
        """Every WEEK-th session counted back from the last one (the latest is always kept)."""
        keep = frame.index[::-1][::WEEK][::-1]
        return frame.loc[keep]

    def _build_points(self, lines: pd.DataFrame) -> list[dict[str, Any]]:
        out = []
        for label, group in lines.groupby("label", sort=False):
            points = [[str(p), self._get_number(v)] for p, v in zip(
                group["period"], group["value"], strict=True)]  # fmt: skip
            out.append({"label": str(label), "points": [p for p in points if p[1] is not None]})
        return out

    @staticmethod
    def _get_number(value: Any) -> float | None:
        if value is None or isinstance(value, str):
            return None
        number = float(value)
        return None if math.isnan(number) else round(number, 3)
