"""Test doubles and frame builders shared by all test modules (no network, no real lake)."""

from __future__ import annotations

import datetime as dt
import subprocess
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
