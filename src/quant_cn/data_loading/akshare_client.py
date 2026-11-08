"""AkShare as a third data source (D-065): official lists and series Tushare lacks or denies."""

from __future__ import annotations

import datetime as dt
import importlib
import logging
import re
from collections.abc import Mapping, Sequence
from types import ModuleType

import pandas as pd

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.clock import Clock
from quant_cn.core.exceptions import DataSourceError

logger = logging.getLogger(__name__)
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class AkshareClient(BaseApiClient):
    """
    Purpose:
        Call one AkShare function per query (`api_name` = function name, `params` = its keyword
        arguments) and return its frame with dates normalised to YYYYMMDD strings, so the lake's
        schema and PIT rules apply unchanged. AkShare scrapes public pages (exchanges, ChinaBond,
        Jin10, Sina): network failures are retried; the library is imported on first use because
        it lives in the optional extra "sources" (D-022, D-065).

    Contract:
        Input:
            clock:         Clock              -- sleeps between retries
            retries:       int >= 0           -- retries after the first failure
            retry_sleep_s: float >= 0         -- pause before each retry
            module:        ModuleType | None  -- the akshare module (tests pass a fake)
        Output:
            instance; `query`
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- registered as source "akshare"

    Test cases:
        TC-AKC-001  calls the named function with params; ISO and date values become YYYYMMDD
        TC-AKC-002  a failing call is retried, then raises DataSourceError; unknown function raises
    """

    def __init__(
        self,
        clock: Clock,
        retries: int = 3,
        retry_sleep_s: float = 6.0,
        module: ModuleType | None = None,
    ) -> None:
        self._clock = clock
        self._retries = retries
        self._retry_sleep_s = retry_sleep_s
        self._module = module

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Run one AkShare function and normalise its dates.

        Contract:
            Input:
                api_name: str                -- akshare function, e.g. "bond_china_yield"
                params:   Mapping[str, str]  -- keyword arguments of that function
                fields:   Sequence[str]      -- ignored (renaming is DatasetSpec.rename)
            Output:
                DataFrame  -- vendor columns; date-like columns as YYYYMMDD strings
            Raises:
                DataSourceError  -- unknown function, or failure after retries
        """
        function = getattr(self._load_module(), api_name, None)
        if not callable(function):
            raise DataSourceError(f"akshare has no function {api_name!r}")
        failures = 0
        while True:
            try:
                frame = function(**dict(params))
                break
            except Exception as exc:
                failures += 1
                if failures > self._retries:
                    raise DataSourceError(
                        f"{api_name}: failed after {failures} attempts: {exc}"
                    ) from exc
                logger.warning("%s attempt %s failed: %s", api_name, failures, exc)
                self._clock.sleep(self._retry_sleep_s)
        if not isinstance(frame, pd.DataFrame):
            raise DataSourceError(f"{api_name}: returned {type(frame).__name__}, not a DataFrame")
        return self._normalize_dates(frame)

    def _load_module(self) -> ModuleType:
        if self._module is None:
            self._module = importlib.import_module("akshare")
        return self._module

    @staticmethod
    def _normalize_dates(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        for column in out.columns:
            series = out[column]
            if pd.api.types.is_datetime64_any_dtype(series):
                out[column] = series.dt.strftime("%Y%m%d")
                continue
            sample = series.dropna()
            if sample.empty:
                continue
            first = sample.iloc[0]
            if isinstance(first, dt.date):
                out[column] = series.map(
                    lambda v: v.strftime("%Y%m%d") if isinstance(v, dt.date) else v
                )
            elif isinstance(first, str) and _ISO_DATE.match(first):
                out[column] = series.map(lambda v: v.replace("-", "") if isinstance(v, str) else v)
        return out
