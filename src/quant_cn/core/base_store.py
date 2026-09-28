"""Extension point for where fetched data is written."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from quant_cn.core.dataset_spec import DatasetSpec


class BaseStore(ABC):
    """
    Purpose:
        Abstract sink for raw fetch results and curated partitions.

    Contract:
        Input:
            (subclass-specific constructor)
        Output:
            instance with `write_raw`, `write_curated`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        lake.ParquetWriter               -- production subclass
        core.BaseFetcher                 -- injected store type
        lake.Compactor                   -- injected store type
        data_loading.FetcherFactory      -- injected store type
        data_loading.DateSweepFetcher    -- injected type or call
        data_loading.EnumFetcher         -- injected type or call
        data_loading.PeriodSweepFetcher  -- injected type or call

    Test cases:
        TC-BAC-001  abstract bases cannot be instantiated
    """

    @abstractmethod
    def write_raw(self, spec: DatasetSpec, key: str, df: pd.DataFrame) -> Path | None:
        """
        Purpose:
            Persist one fetch key's rows atomically.

        Contract:
            Input:
                spec: DatasetSpec
                key:  str        -- fetch key
                df:   DataFrame  -- may be empty
            Output:
                Path | None  -- written file, None when df is empty (nothing written)
            Raises:
                SchemaError  -- a value cannot be coerced to its declared dtype
                LakeError    -- the write failed
        """

    @abstractmethod
    def write_curated(self, spec: DatasetSpec, year: int | None, df: pd.DataFrame) -> Path:
        """
        Purpose:
            Replace one curated partition atomically after validating its schema.

        Contract:
            Input:
                spec: DatasetSpec
                year: int | None  -- partition year; None for unpartitioned datasets
                df:   DataFrame   -- must satisfy spec.build_schema()
            Output:
                Path  -- written file
            Raises:
                SchemaError  -- df violates the schema; nothing is written
                LakeError    -- the write failed
        """
