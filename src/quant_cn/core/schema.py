"""DataFrame contract: columns, dtypes and primary key, enforced at lake boundaries."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import Final, Literal

import pandas as pd

from quant_cn.core.exceptions import SchemaError

TEXT_DTYPE: Final[Literal["string"]] = "string"
NUMBER_DTYPE: Final[Literal["float64"]] = "float64"


class Schema:
    """
    Purpose:
        Declare and enforce a DataFrame shape: text columns are pandas `string`, all other declared
        columns are `float64`, and the primary key is unique and non-null.

    Contract:
        Input:
            name:         str            -- dataset or frame name, used in error messages
            columns:      Sequence[str]  -- declared columns, non-empty, unique
            text_columns: Collection[str]  -- subset of columns stored as text (dates, codes, names)
            primary_key:  Sequence[str]  -- subset of columns; may be empty (no key check)
        Output:
            instance; `coerce`, `validate`, `empty` below
        Raises:
            SchemaError  -- text_columns or primary_key not a subset of columns

    Used by:
        core.DatasetSpec.build_schema          -- builds one Schema per dataset
        lake.ParquetWriter.write_raw     -- coerce dtypes before writing raw files
        lake.ParquetWriter.write_curated -- validate before writing a curated partition
        lake.Compactor.rebuild           -- coerce and select declared columns

    Test cases:
        TC-S-001  coerce casts text to string and numbers to float64
        TC-S-002  strict coerce rejects undeclared columns; missing columns are added as NA
        TC-S-003  unconvertible numeric value raises SchemaError
        TC-S-004  validate rejects wrong column set, wrong dtype, duplicate or null primary key
        TC-S-005  empty() has declared columns and dtypes, zero rows
        TC-S-006  constructor rejects keys or text columns outside columns
    """

    def __init__(
        self,
        name: str,
        columns: Sequence[str],
        text_columns: Collection[str],
        primary_key: Sequence[str],
    ) -> None:
        cols = list(columns)
        if not cols or len(set(cols)) != len(cols):
            raise SchemaError(f"{name}: columns must be non-empty and unique")
        unknown = (set(text_columns) | set(primary_key)) - set(cols)
        if unknown:
            raise SchemaError(f"{name}: key/text columns not declared: {sorted(unknown)}")
        self.name = name
        self.columns = cols
        self.text_columns = frozenset(text_columns)
        self.primary_key = list(primary_key)

    def get_dtype(self, column: str) -> str:
        """
        Purpose:
            Declared dtype name of `column`.

        Contract:
            Input:
                column: str  -- any name; undeclared names are treated as numeric
            Output:
                str  -- "string" or "float64"
            Raises:
                (none)
        """
        return TEXT_DTYPE if column in self.text_columns else NUMBER_DTYPE

    def normalize(self, df: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
        """
        Purpose:
            Return a copy of `df` cast to the declared dtypes.

        Contract:
            Input:
                df:     DataFrame  -- any columns; may be empty
                strict: bool       -- True: output has exactly the declared columns in declared
                                      order (missing ones added as NA, extra ones rejected)
            Output:
                DataFrame  -- same rows; text columns `string`, others `float64`
            Raises:
                SchemaError  -- a value cannot be converted, or strict and undeclared columns exist
        """
        out = df.copy()
        if strict:
            extra = [c for c in out.columns if c not in self.columns]
            if extra:
                raise SchemaError(f"{self.name}: undeclared columns {extra}")
            for col in self.columns:
                if col not in out.columns:
                    out[col] = pd.NA
            out = out[self.columns]
        for col in out.columns:
            out[col] = self._normalize_column(out[col], str(col))
        return out

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Purpose:
            Check `df` satisfies the schema exactly.

        Contract:
            Input:
                df: DataFrame
            Output:
                DataFrame  -- the same frame, unchanged
            Raises:
                SchemaError  -- column set differs, a dtype differs, or the primary key has
                                nulls or duplicates
        """
        if list(df.columns) != self.columns:
            raise SchemaError(f"{self.name}: columns {list(df.columns)} != {self.columns}")
        for col in self.columns:
            ok = (
                pd.api.types.is_string_dtype(df[col])
                if col in self.text_columns
                else pd.api.types.is_float_dtype(df[col])
            )
            if not ok:
                raise SchemaError(
                    f"{self.name}.{col}: dtype {df[col].dtype} != {self.get_dtype(col)}"
                )
        if self.primary_key:
            key = df[self.primary_key]
            if key.isna().any().any():
                raise SchemaError(f"{self.name}: null in primary key {self.primary_key}")
            if key.duplicated().any():
                raise SchemaError(f"{self.name}: duplicate primary key {self.primary_key}")
        return df

    def build_empty(self) -> pd.DataFrame:
        """
        Purpose:
            A zero-row frame with the declared columns and dtypes.

        Contract:
            Input:
                (none)
            Output:
                DataFrame  -- declared columns, zero rows
            Raises:
                (none)
        """
        return pd.DataFrame({c: pd.Series(dtype=self.get_dtype(c)) for c in self.columns})

    def _normalize_column(self, series: pd.Series, column: str) -> pd.Series:
        if column in self.text_columns:
            text: pd.Series = series.astype("string")
            return text
        try:
            number: pd.Series = pd.to_numeric(series, errors="raise").astype("float64")
            return number
        except (ValueError, TypeError) as exc:
            raise SchemaError(f"{self.name}.{column}: not numeric ({exc})") from exc
