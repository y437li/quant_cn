"""Contract tests for portfolio.DeveloperSalesReader (plan 31 ph4)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from quant_cn.core.date_codec import DateCodec
from quant_cn.lake.label_store import LabelStore
from quant_cn.portfolio.developer_sales_reader import DeveloperSalesReader
from quant_cn.portfolio.sector_metric_reader import LINE_COLUMNS
from tests.support import MiniLake

NAMES = {"001979.SZ": "招商蛇口"}


def build_item(metric: str, period: str, value: float, unit: str) -> dict[str, object]:
    return {"metric": metric, "period": period, "value": value, "unit": unit}


def write_briefs(
    store: LabelStore, briefs: list[tuple[str, list[dict[str, object]]]], code: str = "001979.SZ"
) -> None:
    rows = [{"ts_code": code, "doc_key": f"k{i}", "doc_type": "operating_data",
             "period": known, "known_on": known, "source": "test",
             "payload": json.dumps({"items": items}, ensure_ascii=False)}
            for i, (known, items) in enumerate(briefs)]  # fmt: skip
    store.write("operating_data", pd.DataFrame(rows))


# TC-DEV-001
def test_tc_dev_001_monthly_sales(lake: MiniLake) -> None:
    store = LabelStore(lake.writer, lake.lake_root, DateCodec())
    reader = DeveloperSalesReader(store, 36)
    assert reader.read_sales(NAMES).empty
    write_briefs(store, [
        ("20260910", [build_item("签约销售金额", "2026-08", 157.0, "亿元"),
                      build_item("签约销售金额", "2026-01至2026-08", 1200.0, "亿元")]),
        ("20261010", [build_item("签约销售金额", "2026-09", 1432200.0, "万元")]),
        ("20261020", [build_item("签约销售金额", "2026-08", 158.0, "亿元")]),  # restated
    ])  # fmt: skip
    out = reader.read_sales(NAMES)
    assert list(out.columns) == LINE_COLUMNS
    assert out["period"].tolist() == ["2026-08", "2026-09"]
    assert out["value"].tolist() == pytest.approx([158.0, 143.22])
    assert reader.read_ytd_yoy(NAMES).empty  # no prior-year months, no printed YTD (TC-DEV-004)


# TC-DEV-003
def test_tc_dev_003_totals_only(lake: MiniLake) -> None:
    store = LabelStore(lake.writer, lake.lake_root, DateCodec())
    total = build_item("合同销售金额", "2026-08", 8.89, "亿元")
    equity = build_item("权益销售金额", "2026-08", 6.0, "亿元")
    province = build_item("销售金额", "2026-08", 23635.0, "万元") | {"segment": "江苏"}
    write_briefs(store, [("20260912", [total, equity, province])])
    out = DeveloperSalesReader(store, 36).read_sales(NAMES)
    assert out["value"].tolist() == pytest.approx([8.89])


# TC-DEV-002
def test_tc_dev_002_land_intensity(lake: MiniLake) -> None:
    store = LabelStore(lake.writer, lake.lake_root, DateCodec())
    reader = DeveloperSalesReader(store, 36)
    assert reader.read_land_intensity(NAMES).empty
    briefs = []
    for m in range(1, 13):  # the brief filed on the 10th of month m + 1 reports month m
        known = f"2026{m + 1:02d}10" if m < 12 else "20270110"
        items = [build_item("签约销售金额", f"2026-{m:02d}", 100.0, "亿元")]
        if m in (3, 9):  # two parcels with the same range; total and equity price
            items += [
                build_item("公司需支付价款", f"2026-{m:02d}至2026-{m:02d}", 200000.0, "万元"),
                build_item("公司需支付价款", f"2026-{m:02d}至2026-{m:02d}", 100000.0, "万元"),
                build_item("需支付权益地价", f"2026-{m:02d}", 10.0, "亿元"),
            ]
        briefs.append((known, items))
    write_briefs(store, briefs)
    out = reader.read_land_intensity(NAMES)
    assert out["period"].tolist() == ["2026-12"]
    assert out["value"].iloc[-1] == pytest.approx(5.0)  # (30 + 30) / 1,200


# TC-DEV-004
def test_tc_dev_004_sales_yoy(lake: MiniLake) -> None:
    store = LabelStore(lake.writer, lake.lake_root, DateCodec())
    reader = DeveloperSalesReader(store, 36)
    briefs = []
    for year, level in ((2025, 100.0), (2026, 80.0)):
        for m in range(1, 11):
            if (year, m) == (2026, 1):
                continue  # January missing in 2026: no rolling window touches it below
            items = [build_item("签约金额", f"{year}-{m:02d}", level, "亿元")]
            if m >= 2:
                items.append(
                    build_item("签约金额", f"{year}-01至{year}-{m:02d}", level * m, "亿元")
                )
            briefs.append((f"{year}{m + 1:02d}10", items))
    write_briefs(store, briefs)
    yoy = reader.read_sales_yoy(NAMES)
    assert yoy["period"].tolist() == [f"2026-{m:02d}" for m in range(4, 11)]  # 01-03 lack months
    assert yoy["value"].tolist() == pytest.approx([-20.0] * 7)
    ytd = reader.read_ytd_yoy(NAMES)
    assert ytd.values.tolist() == [["招商蛇口", "2026-10", pytest.approx(-20.0)]]
    # a developer whose last brief is 2026-03 (7 months behind) is dropped from the YTD rows
    old = [(f"{y}0410", [build_item("签约金额", f"{y}-01至{y}-03", 50.0, "亿元"),
                         build_item("签约金额", f"{y}-03", 10.0, "亿元")])
           for y in (2025, 2026)]  # fmt: skip
    vanke = [{"ts_code": "000002.SZ", "doc_key": f"v{i}", "doc_type": "operating_data",
              "period": k, "known_on": k, "source": "test",
              "payload": json.dumps({"items": items}, ensure_ascii=False)}
             for i, (k, items) in enumerate(old)]  # fmt: skip
    store.write("operating_data", pd.concat([store.read("operating_data"), pd.DataFrame(vanke)]))
    both = reader.read_ytd_yoy({**NAMES, "000002.SZ": "万科A"})
    assert both["label"].tolist() == ["招商蛇口"]
    alone = reader.read_ytd_yoy({"000002.SZ": "万科A"})  # on its own it is the newest
    assert alone.values.tolist() == [["万科A", "2026-03", pytest.approx(0.0)]]
