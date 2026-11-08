"""BaoStock as a verification-only source (D-065, D-085): closes and adjustment factors."""

from __future__ import annotations

import contextlib
import importlib
import logging
from collections.abc import Mapping, Sequence
from types import ModuleType
from typing import Any

import pandas as pd

from quant_cn.core.base_api_client import BaseApiClient
from quant_cn.core.clock import Clock
from quant_cn.core.exceptions import DataSourceError

logger = logging.getLogger(__name__)
_EXCHANGES = {"SH": "sh", "SZ": "sz"}
_DATE_COLUMNS = ("date", "dividOperateDate")
_VENDOR_FIELDS = {"trade_date": "date", "ts_code": "code"}  # lake name -> BaoStock name
_YYYYMMDD = 8
_SYMBOL_LEN = 6
LOGIN_BACKOFF = 5  # login retries wait 5x the query retry pause


class BaostockClient(BaseApiClient):
    """
    Purpose:
        Call one BaoStock query per request (`api_name` = method, e.g. query_history_k_data_plus)
        and return a frame in lake conventions: `ts_code` param converted to BaoStock's code
        ("600000.SH" -> "sh.600000") and back in the result, YYYYMMDD dates in and out, numeric
        strings as floats. Logs in once on first use; BaoStock is in the optional extra "sources"
        and is imported lazily. Verification only: its datasets never replace Tushare's (D-065).

    Contract:
        Input:
            clock:         Clock              -- sleeps between retries
            retries:       int >= 0           -- retries after the first failed query
            retry_sleep_s: float >= 0
            module:        ModuleType | None  -- the baostock module (tests pass a fake)
        Output:
            instance; `query`
        Raises:
            (none at construction)

    Used by:
        cli.ServiceBuilder  -- registered as source "baostock"

    Test cases:
        TC-BSC-001  codes and dates are converted both ways; fields are joined; numbers parsed
        TC-BSC-002  error codes are retried then raise DataSourceError; login happens once
        TC-BSC-004  a failed login is retried before the query runs
        TC-BSC-003  a Beijing or non-6-digit code (T600018.SH) returns an empty frame, no call
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
        self._logged_in = False

    def query(
        self, api_name: str, params: Mapping[str, str], fields: Sequence[str]
    ) -> pd.DataFrame:
        """
        Purpose:
            Run one BaoStock query for one security.

        Contract:
            Input:
                api_name: str                -- BaoStock method name
                params:   Mapping[str, str]  -- ts_code, start_date, end_date (YYYYMMDD) + extras
                fields:   Sequence[str]      -- k-data fields; trade_date/ts_code map to
                                                BaoStock's date/code
            Output:
                DataFrame  -- BaoStock columns; ts_code column; dates YYYYMMDD; numbers float
            Raises:
                DataSourceError  -- unknown method, or an error code after retries
        """
        args = dict(params)
        ts_code = args.pop("ts_code", "")
        code = self._to_code(ts_code)
        if code is None:
            return pd.DataFrame()
        args = {k: self._to_iso(v) if k.endswith("_date") else v for k, v in args.items()}
        if api_name == "query_history_k_data_plus":
            args["fields"] = ",".join(_VENDOR_FIELDS.get(f, f) for f in fields)
        frame = self._run(api_name, code, args)
        return self._normalize(frame, ts_code)

    def _run(self, api_name: str, code: str, args: dict[str, str]) -> pd.DataFrame:
        module = self._load_module()
        method = getattr(module, api_name, None)
        if not callable(method):
            raise DataSourceError(f"baostock has no method {api_name!r}")
        failures = 0
        while True:
            result = method(code=code, **args)
            if str(result.error_code) == "0":
                return pd.DataFrame(result.get_data())
            failures += 1
            if failures > self._retries:
                raise DataSourceError(f"{api_name} {code}: {result.error_code} {result.error_msg}")
            logger.warning("%s %s attempt %s: %s", api_name, code, failures, result.error_msg)
            self._clock.sleep(self._retry_sleep_s)
            self._logged_in = False
            self._load_module()

    def _load_module(self) -> ModuleType:
        if self._module is None:
            self._module = importlib.import_module("baostock")
        failures = 0
        while not self._logged_in:
            login: Any = self._module.login()
            if str(login.error_code) == "0":
                self._logged_in = True
                break
            failures += 1  # network errors ("网络接收错误") also hit login: same retry budget
            if failures > self._retries:
                raise DataSourceError(f"baostock login failed: {login.error_msg}")
            logger.warning("baostock login attempt %s failed: %s", failures, login.error_msg)
            self._clock.sleep(self._retry_sleep_s * LOGIN_BACKOFF)
            with contextlib.suppress(Exception):  # a broken session must be closed before re-login
                self._module.logout()
        return self._module

    @staticmethod
    def _to_code(ts_code: str) -> str | None:
        symbol, _, exchange = ts_code.partition(".")
        prefix = _EXCHANGES.get(exchange)
        valid = prefix and len(symbol) == _SYMBOL_LEN and symbol.isdigit()  # T600018.SH: no
        return f"{prefix}.{symbol}" if valid else None

    @staticmethod
    def _to_iso(value: str) -> str:
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}" if len(value) == _YYYYMMDD else value

    @staticmethod
    def _normalize(frame: pd.DataFrame, ts_code: str) -> pd.DataFrame:
        out = frame.copy()
        for column in out.columns:
            if column in _DATE_COLUMNS:
                out[column] = out[column].str.replace("-", "", regex=False)
            elif column != "code":
                converted = pd.to_numeric(out[column], errors="coerce")
                if converted.notna().sum() == out[column].replace("", pd.NA).notna().sum():
                    out[column] = converted
        if "code" in out.columns:
            out = out.drop(columns="code")
        out.insert(0, "ts_code", ts_code)
        return out
