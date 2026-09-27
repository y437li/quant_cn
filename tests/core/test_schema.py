from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.core.exceptions import SchemaError
from quant_cn.core.schema import Schema


@pytest.fixture
def schema() -> Schema:
    return Schema(
        "bars",
        ["ts_code", "trade_date", "close"],
        ["ts_code", "trade_date"],
        ["ts_code", "trade_date"],
    )


def frame(**cols: list[object]) -> pd.DataFrame:
    return pd.DataFrame(cols)


# TC-S-001
def test_tc_s_001_coerce_dtypes(schema: Schema) -> None:
    out = schema.coerce(frame(ts_code=["A"], trade_date=["20260828"], close=["10.5"]))
    assert pd.api.types.is_string_dtype(out["ts_code"])
    assert out["close"].dtype == "float64"
    assert out["close"].iloc[0] == pytest.approx(10.5)


# TC-S-002
def test_tc_s_002_strict_columns(schema: Schema) -> None:
    out = schema.coerce(frame(trade_date=["20260828"], ts_code=["A"]), strict=True)
    assert list(out.columns) == ["ts_code", "trade_date", "close"]
    assert out["close"].isna().all()
    with pytest.raises(SchemaError):
        schema.coerce(frame(ts_code=["A"], trade_date=["x"], close=[1.0], extra=[1]), strict=True)


# TC-S-003
def test_tc_s_003_not_numeric(schema: Schema) -> None:
    with pytest.raises(SchemaError):
        schema.coerce(frame(ts_code=["A"], trade_date=["x"], close=["abc"]))


# TC-S-004
def test_tc_s_004_validate(schema: Schema) -> None:
    good = schema.coerce(
        frame(ts_code=["A", "B"], trade_date=["1", "1"], close=[1.0, 2.0]), strict=True
    )
    schema.validate(good)
    with pytest.raises(SchemaError):
        schema.validate(good[["close", "ts_code", "trade_date"]])
    with pytest.raises(SchemaError):
        schema.validate(good.assign(close=good["close"].astype("string")))
    with pytest.raises(SchemaError):
        schema.validate(pd.concat([good, good]))
    with pytest.raises(SchemaError):
        schema.validate(good.assign(ts_code=pd.Series([None, "B"], dtype="string")))


# TC-S-005
def test_tc_s_005_empty(schema: Schema) -> None:
    empty = schema.empty()
    assert list(empty.columns) == schema.columns and empty.empty
    schema.validate(empty)


# TC-S-006
def test_tc_s_006_bad_declaration() -> None:
    with pytest.raises(SchemaError):
        Schema("x", ["a"], ["b"], [])
    with pytest.raises(SchemaError):
        Schema("x", ["a"], [], ["b"])
    with pytest.raises(SchemaError):
        Schema("x", [], [], [])
