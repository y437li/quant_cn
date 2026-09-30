"""Test doubles and frame builders shared by all test modules (no network, no real lake)."""

from __future__ import annotations

import datetime as dt
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import numpy as np
import pandas as pd

from quant_cn.calculation.black76_model import Black76Model
from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.base_step import BaseStep, ProgressHook
from quant_cn.core.clock import Clock
from quant_cn.core.config import Config, UniverseConfig
from quant_cn.core.dataset_spec import CuratedSpec, DatasetSpec, SweepSpec
from quant_cn.core.exceptions import QuantCnError
from quant_cn.core.step_report import StepReport
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.run_log import RunLog
from quant_cn.pipeline.universe_step import UniverseStep


class FakeClock(Clock):
    """Fixed wall time; sleeps are recorded, monotonic advances 1 ms per call."""

    def __init__(self, today: str = "20260830") -> None:
        self._now = dt.datetime.strptime(today, "%Y%m%d").replace(hour=18)
        self._tick = 0.0
        self.sleeps: list[float] = []

    def get_now(self) -> dt.datetime:
        return self._now

    def get_monotonic(self) -> float:
        self._tick += 0.001
        return self._tick

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)


class FakeTushareClient(BaseApiClient):
    """Canned frames per (api, key param); scripted exceptions; records every call."""

    def __init__(self) -> None:
        self.frames: dict[tuple[str, str], pd.DataFrame] = {}
        self.errors: dict[tuple[str, str], Exception] = {}
        self.calls: list[tuple[str, dict[str, str]]] = []

    def add(self, api: str, key: str, df: pd.DataFrame) -> None:
        self.frames[(api, key)] = df

    def add_failure(self, api: str, key: str, exc: Exception) -> None:
        self.errors[(api, key)] = exc

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        self.calls.append((api_name, dict(params)))
        key = self._get_key(params)
        if (api_name, key) in self.errors:
            raise self.errors.pop((api_name, key))
        return self.frames.get((api_name, key), pd.DataFrame(columns=list(fields)))

    @staticmethod
    def _get_key(params: Mapping[str, str]) -> str:
        for name in ("trade_date", "period", "ann_date", "list_status", "ts_code"):
            if name in params:
                return params[name]
        return "all"


@dataclass
class MiniLake:
    lake_root: Path
    catalog: LakeCatalog
    writer: ParquetWriter
    fetch_log: FetchLog
    run_log: RunLog
    query: LakeQuery
    clock: FakeClock


class Sample:
    """Small deterministic frames and specs built in code."""

    @staticmethod
    def build_spec(**overrides: object) -> DatasetSpec:
        """A small daily-style spec for unit tests."""
        base: dict[str, object] = {
            "name": "bars",
            "endpoint": "daily",
            "sweep": SweepSpec(kind="trade_date"),
            "primary_key": ["ts_code", "trade_date"],
            "known_on": "trade_date",
            "fields": ["ts_code", "trade_date", "close"],
            "text_fields": ["ts_code", "trade_date"],
            "curated": CuratedSpec(path="bars", partition_by="trade_date"),
        }
        base.update(overrides)
        return DatasetSpec(**base)  # type: ignore[arg-type]

    @staticmethod
    def build_bars(
        trade_date: str, codes: Sequence[str] = ("000001.SZ", "600000.SH")
    ) -> pd.DataFrame:
        """Daily-style rows for one day."""
        return pd.DataFrame(
            {
                "ts_code": list(codes),
                "trade_date": trade_date,
                "close": [10.0 + i for i in range(len(codes))],
            }
        )

    @staticmethod
    def build_trade_cal(open_days: Sequence[str], closed_days: Sequence[str] = ()) -> pd.DataFrame:
        """trade_cal rows: given open and closed days."""
        rows = [(d, 1, "") for d in open_days] + [(d, 0, "") for d in closed_days]
        return pd.DataFrame(rows, columns=["cal_date", "is_open", "pretrade_date"]).sort_values(
            "cal_date"
        )


class SampleRepo:
    """A throwaway git working tree in tmp_path with the given files (for core.docs checkers)."""

    @staticmethod
    def build_repo(root: Path, files: dict[str, str]) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        for rel, text in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        return root


class SampleLake:
    """Raw inputs for derived-view and PIT tests, written through the real writer."""

    OPEN = (
        "20260105",
        "20260106",
        "20260320",
        "20260323",
        "20260410",
        "20260413",
        "20260415",
        "20260416",
        "20260424",
        "20260427",
        "20260428",
    )

    @staticmethod
    def write_calendar(lake: MiniLake, spec: DatasetSpec) -> None:
        lake.writer.write_raw(spec, "all", Sample.build_trade_cal(SampleLake.OPEN))

    @staticmethod
    def write_income(
        lake: MiniLake, spec: DatasetSpec, rows: list[tuple[str, str, str, float]]
    ) -> None:
        """rows: (end_date, f_ann_date, report_type, total_profit) for 000001.SZ."""
        records = []
        for end_date, f_ann_date, report_type, profit in rows:
            record: dict[str, object] = {f: None for f in spec.fields}
            record.update(
                ts_code="000001.SZ",
                end_date=end_date,
                ann_date=f_ann_date,
                f_ann_date=f_ann_date,
                update_flag="1",
                report_type=report_type,
                total_profit=profit,
            )
            records.append(record)
        lake.writer.write_raw(spec, "20260331", pd.DataFrame(records))


class SampleOptions:
    """Synthetic option data priced with Black-76 at a flat volatility (known-answer VIX inputs)."""

    SHIBOR = pd.DataFrame(
        [["20260801", 1.4, 1.4, 1.4, 1.4, 1.45, 1.5, 1.5, 1.5]],
        columns=["date", "on", "1w", "2w", "1m", "3m", "6m", "9m", "1y"],
    )

    @staticmethod
    def build_chain(
        trade_date: str = "20260828",
        expiries: tuple[tuple[str, int], ...] = (("20260923", 26), ("20261028", 61)),
        strikes: Sequence[float] = tuple(round(1.5 + 0.05 * i, 2) for i in range(71)),
        sigma: float = 0.20,
        forward: float = 3.04,
    ) -> pd.DataFrame:
        model, rows = Black76Model(), []
        for expiry, days in expiries:
            for k in strikes:
                for side in ("C", "P"):
                    price = model.compute_price(forward, k, days / 365, 0.014, sigma, side)
                    rows.append(
                        {
                            "trade_date": trade_date,
                            "opt_code": "OPTEST",
                            "ts_code": f"{expiry}{side}{k}",
                            "call_put": side,
                            "strike": k,
                            "maturity_date": expiry,
                            "days": days,
                            "close": price,
                            "settle": float("nan"),
                            "vol": 1.0,
                            "oi": 1.0,
                            "adjusted": False,
                        }
                    )
        return pd.DataFrame(rows)


class ScriptStep(BaseStep):
    def __init__(self, name: str, error: QuantCnError | None = None) -> None:
        self._name = name
        self._error = error
        self.ran = False

    @property
    def name(self) -> str:
        return self._name

    def list_units(self) -> list[str]:
        return ["k"]

    def run(self, run_id: str, progress: ProgressHook | None = None) -> StepReport:
        self.ran = True
        if self._error:
            raise self._error
        if progress:
            progress("k", "fetched")
        return StepReport(self._name, fetched=1)


class SampleFactorLake:
    """Statements, prices and daily_basic for one stock (plan 04 factor PIT tests)."""

    CODE = "000001.SZ"
    PROFIT: ClassVar[
        list[tuple[str, str, float]]
    ] = [  # (end_date, f_ann_date, n_income_attr_p YTD)
        ("20240331", "20240425", 10.0),
        ("20241231", "20250320", 80.0),
        ("20250331", "20250425", 20.0),
        ("20251231", "20260320", 100.0),
        ("20260331", "20260424", 30.0),
        ("20251231", "20260515", 120.0),  # restated FY 2025
    ]

    @staticmethod
    def write(lake: MiniLake, config: Config, name: str, rows: list[dict[str, object]]) -> None:
        spec = config.get_dataset(name)
        base = {f: None for f in spec.fields}
        lake.writer.write_raw(spec, "x", pd.DataFrame([base | r for r in rows]))
        Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(spec)

    @classmethod
    def write_market(cls, lake: MiniLake, config: Config, days: list[str]) -> None:
        lake.writer.write_raw(config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(days))
        Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(
            config.get_dataset("trade_cal")
        )
        cls.write(
            lake,
            config,
            "stock_basic",
            [{"ts_code": cls.CODE, "list_status": "L", "list_date": "20000101"}],
        )
        cls.write(
            lake,
            config,
            "daily",
            [{"ts_code": cls.CODE, "trade_date": d, "open": 10.0, "close": 10.0} for d in days],
        )
        cls.write(
            lake,
            config,
            "adj_factor",
            [{"ts_code": cls.CODE, "trade_date": d, "adj_factor": 1.0} for d in days],
        )
        cls.write(
            lake,
            config,
            "daily_basic",
            [
                {"ts_code": cls.CODE, "trade_date": d, "total_mv": 50.0, "turnover_rate_f": 1.0}
                for d in days
            ],
        )

    @classmethod
    def write_statements(cls, lake: MiniLake, config: Config) -> None:
        stmt = {"ts_code": cls.CODE, "report_type": "1", "update_flag": "1"}
        cls.write(
            lake,
            config,
            "income_vip",
            [
                stmt | {"end_date": e, "ann_date": a, "f_ann_date": a, "n_income_attr_p": v}
                for e, a, v in cls.PROFIT
            ],
        )
        cls.write(
            lake,
            config,
            "balancesheet_vip",
            [
                stmt
                | {
                    "end_date": "20260331",
                    "ann_date": "20260424",
                    "f_ann_date": "20260424",
                    "total_hldr_eqy_exc_min_int": 1000.0,
                }
            ],
        )


class SampleMarket:
    """A small market (prices, daily_basic, universe) for feature and evaluation step tests."""

    DAYS: ClassVar[list[str]] = pd.bdate_range("2026-01-05", periods=80).strftime("%Y%m%d").tolist()
    CODES: ClassVar[list[str]] = [f"{i:06d}.SH" for i in range(39)] + ["830001.BJ"]

    @classmethod
    def write(cls, lake: MiniLake, config: Config) -> None:
        rng = np.random.default_rng(3)
        write = SampleFactorLake.write
        lake.writer.write_raw(
            config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(cls.DAYS)
        )
        Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(
            config.get_dataset("trade_cal")
        )
        write(
            lake,
            config,
            "stock_basic",
            [{"ts_code": c, "list_status": "L", "list_date": "20000101"} for c in cls.CODES],
        )
        close = 10 * np.cumprod(
            1 + 0.02 * rng.standard_normal((len(cls.DAYS), len(cls.CODES))), axis=0
        )
        bars, basic = [], []
        for t, day in enumerate(cls.DAYS):
            for i, code in enumerate(cls.CODES):
                opened = close[t - 1, i] if t else close[0, i]
                bars.append(
                    {"ts_code": code, "trade_date": day, "open": opened, "close": close[t, i]}
                )
                basic.append(
                    {
                        "ts_code": code,
                        "trade_date": day,
                        "total_mv": 100.0 + i,
                        "turnover_rate_f": float(rng.uniform(0.5, 5.0)),
                    }
                )
        cls.write_market(lake, config, bars, basic)
        views = DerivedViews(lake.catalog, lake.query, config.datasets)
        views.refresh()
        rules = UniverseConfig(start=cls.DAYS[0], min_sessions=1, exchanges=["SH", "SZ"])
        UniverseStep(lake.query, lake.writer, rules).run("r0")
        views.refresh_tables()

    @classmethod
    def write_market(
        cls,
        lake: MiniLake,
        config: Config,
        bars: list[dict[str, object]],
        basic: list[dict[str, object]],
    ) -> None:
        write = SampleFactorLake.write
        write(lake, config, "daily", bars)
        adj = [
            {"ts_code": b["ts_code"], "trade_date": b["trade_date"], "adj_factor": 1.0}
            for b in bars
        ]
        write(lake, config, "adj_factor", adj)
        write(lake, config, "daily_basic", basic)
        names = [{"ts_code": c, "name": "x", "start_date": "20000101"} for c in cls.CODES]
        write(lake, config, "namechange", names)
