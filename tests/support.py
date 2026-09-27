"""Test doubles and frame builders shared by all test modules (no network, no real lake)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.clock import Clock
from quant_cn.core.dataset_spec import CuratedSpec, DatasetSpec, SweepSpec
from quant_cn.lake.fetch_log import FetchLog
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter
from quant_cn.lake.run_log import RunLog


class FakeClock(Clock):
    """Fixed wall time; sleeps are recorded, monotonic advances 1 ms per call."""

    def __init__(self, today: str = "20260830") -> None:
        self._now = dt.datetime.strptime(today, "%Y%m%d").replace(hour=18)
        self._tick = 0.0
        self.sleeps: list[float] = []

    def now(self) -> dt.datetime:
        return self._now

    def monotonic(self) -> float:
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

    def fail(self, api: str, key: str, exc: Exception) -> None:
        self.errors[(api, key)] = exc

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        self.calls.append((api_name, dict(params)))
        key = self._key(params)
        if (api_name, key) in self.errors:
            raise self.errors.pop((api_name, key))
        return self.frames.get((api_name, key), pd.DataFrame(columns=list(fields)))

    @staticmethod
    def _key(params: Mapping[str, str]) -> str:
        for name in ("trade_date", "period", "ann_date", "list_status", "ts_code"):
            if name in params:
                return params[name]
        return "all"


@dataclass
class MiniLake:
    root: Path
    catalog: LakeCatalog
    writer: ParquetWriter
    fetch_log: FetchLog
    run_log: RunLog
    query: LakeQuery
    clock: FakeClock


class Build:
    """Small deterministic frames and specs built in code."""

    @staticmethod
    def spec(**overrides: object) -> DatasetSpec:
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
    def bars(trade_date: str, codes: Sequence[str] = ("000001.SZ", "600000.SH")) -> pd.DataFrame:
        """Daily-style rows for one day."""
        return pd.DataFrame(
            {
                "ts_code": list(codes),
                "trade_date": trade_date,
                "close": [10.0 + i for i in range(len(codes))],
            }
        )

    @staticmethod
    def trade_cal(open_days: Sequence[str], closed_days: Sequence[str] = ()) -> pd.DataFrame:
        """trade_cal rows: given open and closed days."""
        rows = [(d, 1, "") for d in open_days] + [(d, 0, "") for d in closed_days]
        return pd.DataFrame(rows, columns=["cal_date", "is_open", "pretrade_date"]).sort_values(
            "cal_date"
        )
