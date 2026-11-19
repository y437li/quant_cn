"""Derived year tables keyed by a date column: replace dates, read years (plan 21)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from quant_cn.core.exceptions import LakeError
from quant_cn.lake.parquet_writer import ParquetWriter

_PART = "part-0.parquet"


class DatedTableStore:
    """
    Purpose:
        Own materialised derived tables (derived/<name>/year=YYYY/part-0.parquet) keyed by a
        YYYYMMDD date column, read and written without the DuckDB catalog so a read-only
        session can update them (plan 21):
        - `write`: the rows of the dates being written replace the stored rows of those
          dates; the other dates of each year are kept;
        - `read`: the stored rows of some years (empty frame when none);
        - `read_report`: one whole table under derived/ (e.g. a report written with
          ParquetWriter.write_table).
        The derived views over these tables are refreshed separately (DerivedViews).

    Contract:
        Input:
            writer: ParquetWriter  -- write_derived; lake_root
        Output:
            instance; `write(name, frame, date_column)` -> list[Path];
            `read(name, years)` -> DataFrame; `read_report(rel_path)` -> DataFrame
        Raises:
            (none at construction)

    Used by:
        factor.FactorFactory  -- retail_gauge readings for RetailGaugeFactor
        cli.ServiceBuilder  -- wires it into FactorFactory
        portfolio.OpportunityScreen  -- derived/opportunity_list
        calculation.RetailGaugeFeatureBuilder  -- derived/retail_gauge_features
        calculation.RetailGaugeNowcaster       -- derived/retail_gauge, the backtest report
        cli.GaugeCommands                      -- wires it

    Test cases:
        TC-DTW-001  writing a date twice keeps only the second rows; other dates of the year
                    are kept; rows of two years go to two files; read returns them
        TC-DTW-002  read of a missing table is empty; read_report of a missing file raises
                    LakeError
    """

    def __init__(self, writer: ParquetWriter) -> None:
        self._writer = writer
        self._root = writer.lake_root / "derived"

    def write(self, name: str, frame: pd.DataFrame, date_column: str) -> list[Path]:
        """
        Purpose:
            Replace the frame's dates in the year files of derived/<name>.

        Contract:
            Input:
                name:        str        -- folder under derived/
                frame:       DataFrame  -- has date_column (YYYYMMDD str) and ts_code
                date_column: str
            Output:
                list[Path]  -- year files written, sorted by (date_column, ts_code)
            Raises:
                LakeError  -- read or write failure
        """
        paths = []
        for year, rows in frame.groupby(frame[date_column].str[:4]):
            old = self.read(name, [str(year)])
            if not old.empty:
                old = old[~old[date_column].isin(rows[date_column].unique())]
            part = pd.concat([old, rows], ignore_index=True) if not old.empty else rows
            part = part.sort_values([date_column, "ts_code"]).reset_index(drop=True)
            paths.append(self._writer.write_derived(name, int(str(year)), part))
        return paths

    def read(self, name: str, years: Sequence[str]) -> pd.DataFrame:
        """
        Purpose:
            Stored rows of derived/<name> for some years.

        Contract:
            Input:
                name:  str            -- folder under derived/
                years: Sequence[str]  -- YYYY
            Output:
                DataFrame  -- empty (no columns) when no year file exists
            Raises:
                LakeError  -- unreadable file
        """
        files = [self._root / name / f"year={y}" / _PART for y in years]
        frames = [self._read_file(f) for f in files if f.exists()]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def read_report(self, rel_path: str) -> pd.DataFrame:
        """
        Purpose:
            A whole table under derived/.

        Contract:
            Input:
                rel_path: str  -- path below derived/, ending in .parquet
            Output:
                DataFrame
            Raises:
                LakeError  -- missing or unreadable file
        """
        path = self._root / rel_path
        if not path.exists():
            raise LakeError(f"{path} missing")
        return self._read_file(path)

    @staticmethod
    def _read_file(path: Path) -> pd.DataFrame:
        try:
            return pd.read_parquet(path)
        except (OSError, ValueError) as exc:
            raise LakeError(f"cannot read {path}: {exc}") from exc
