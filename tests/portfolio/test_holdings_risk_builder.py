"""Contract tests for portfolio.HoldingsRiskBuilder and core.PositionsBook (plan 15 phase 7d)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import ConfigError, LakeError
from quant_cn.core.positions_book import Position, PositionsBook
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.portfolio.holdings_history_writer import HoldingsHistoryWriter
from quant_cn.portfolio.holdings_risk_builder import HoldingsRiskBuilder
from quant_cn.risk.base_risk_model import BaseRiskModel
from quant_cn.risk.risk_decomposer import RiskDecomposer
from quant_cn.risk.risk_snapshot import RiskSnapshot
from tests.support import MiniLake, SampleFactorLake

A, B, C, GONE = "000001.SZ", "600000.SH", "300001.SZ", "000002.SZ"
DAY = "20261111"
FACTORS = ["country", "ind_801010.SI", "size"]
X = pd.DataFrame(
    [[1.0, 1.0, 0.5], [1.0, 0.0, -1.0], [1.0, 1.0, 0.0]], index=[A, B, C], columns=FACTORS
)
COV = pd.DataFrame(
    [[1e-4, 2e-5, 0.0], [2e-5, 4e-5, 0.0], [0.0, 0.0, 9e-6]], index=FACTORS, columns=FACTORS
)
SPEC = pd.Series([0.02, 0.015, 0.03], index=[A, B, C])
CLOSE = {A: 10.0, B: 20.0, C: 5.0}


class FixedModel(BaseRiskModel):
    """One snapshot for every session."""

    def load_snapshot(self, trade_date: str) -> RiskSnapshot:
        return RiskSnapshot(trade_date, X, COV, SPEC)


BOOK = PositionsBook(
    as_of=DAY,
    cash=1000.0,
    positions=[
        Position(code=A, name="a", shares=100, cost=8.0),
        Position(code=B, name="b", shares=50, cost=25.0),
        Position(code=C, name="c", shares=200, cost=5.0),
        Position(code=GONE, name="gone", shares=10, cost=1.0),
    ],
)


def _write(lake: MiniLake, config: Config) -> None:
    rows = [{"ts_code": c, "trade_date": DAY, "close": v} for c, v in CLOSE.items()]
    SampleFactorLake.write(lake, config, "daily", rows)
    weights = [
        {"index_code": "000300.SH", "con_code": c, "trade_date": DAY, "weight": 50.0}
        for c in (A, B)
    ]
    SampleFactorLake.write(lake, config, "index_weight", weights)
    spec = pd.DataFrame(
        {
            "trade_date": DAY,
            "ts_code": SPEC.index,
            "sigma": SPEC.values,
            "sigma_raw": 0.0,
            "method": "x",
        }
    )
    lake.writer.write_derived("risk_specific_risk", 2026, spec)
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh_tables()


def _build_builder(lake: MiniLake, book: PositionsBook = BOOK) -> HoldingsRiskBuilder:
    return HoldingsRiskBuilder(
        book,
        lake.query,
        FixedModel("m"),
        RiskDecomposer(),
        HoldingsHistoryWriter(lake.query, lake.writer),
        "000300.SH",
    )


@pytest.fixture
def doc(lake: MiniLake, config: Config) -> dict:
    _write(lake, config)
    return _build_builder(lake).build("20261112")


# TC-HRB-001
def test_tc_hrb_001_values_and_risk(doc: dict) -> None:
    value = 100 * 10 + 50 * 20 + 200 * 5 + 1000.0
    pos = {p["code"]: p for p in doc["positions"]}
    assert doc["as_of"] == DAY and doc["value"] == pytest.approx(value)
    assert pos[A]["weight"] == pytest.approx(1000 / value)
    assert pos[B]["pnl"] == pytest.approx(50 * (20 - 25))
    assert pos[A]["pnl_pct"] == pytest.approx(10 / 8 - 1)
    w = pd.Series({A: 1000 / value, B: 1000 / value, C: 1000 / value})
    factor, spec = RiskSnapshot(DAY, X, COV, SPEC).compute_variance(w)
    assert doc["risk"]["total"] == pytest.approx(math.sqrt((factor + spec) * 252), abs=1e-6)
    assert doc["risk"]["factor"] == pytest.approx(math.sqrt(factor * 252), abs=1e-6)
    assert doc["risk"]["active_total"] is not None
    size = next(f for f in doc["factors"] if f["factor"] == "size")
    assert size["exposure"] == pytest.approx((0.5 - 1.0) / 4, abs=1e-6)
    assert size["kind"] == "style"


# TC-HRB-002
def test_tc_hrb_002_contributions_correlation_missing(doc: dict) -> None:
    contrib = [p["contrib"] for p in doc["positions"] if p["contrib"] is not None]
    assert sum(contrib) == pytest.approx(1.0, abs=1e-5)
    m = np.array(doc["correlation"]["matrix"])
    assert np.diag(m) == pytest.approx(1.0) and doc["correlation"]["codes"] == [A, B, C]
    assert doc["missing"] == [GONE]
    gone = next(p for p in doc["positions"] if p["code"] == GONE)
    assert gone["close"] is None and gone["weight"] is None
    se = doc["stock_exposures"]
    assert se["styles"] == ["size"]
    assert [(r["code"], r["industry"], r["values"]) for r in se["rows"]] == [
        (A, "ind_801010.SI", [0.5]),
        (B, "", [-1.0]),
        (C, "ind_801010.SI", [0.0]),
    ]


# TC-HRB-003
def test_tc_hrb_003_history_replaces_session(
    lake: MiniLake, config: Config, tmp_path: Path
) -> None:
    _write(lake, config)
    builder = _build_builder(lake)
    builder.write(tmp_path, "20261112")
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh_tables()
    builder.write(tmp_path, "20261112")
    rows = lake.query.sql("SELECT * FROM derived.holdings_positions")
    assert len(rows) == 5 and set(rows["code"]) == {A, B, C, GONE, "CASH"}
    risk = lake.query.sql("SELECT * FROM derived.holdings_risk WHERE component = 'total'")
    assert len(risk) == 1
    assert json.loads((tmp_path / "holdings_risk.json").read_text(encoding="utf-8"))["as_of"] == DAY


# TC-HRB-004
def test_tc_hrb_004_empty_and_errors(lake: MiniLake, config: Config, tmp_path: Path) -> None:
    empty = _build_builder(lake, PositionsBook()).build(DAY)
    assert empty["as_of"] == "" and empty["positions"] == []
    _write(lake, config)
    with pytest.raises(LakeError):
        _build_builder(lake).build("20200101")
    with pytest.raises(LakeError):
        _build_builder(lake).write(tmp_path / "absent", DAY)


# TC-PB-001
def test_tc_pb_001_book_loads(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "local.positions.yaml").write_text(
        "as_of: '20261112'\ncash: 5\npositions:\n"
        "  - {code: A, name: x, shares: 100, cost: 2.5, last: 3, market_value: 300}\n",
        encoding="utf-8",
    )
    book = PositionsBook.load(tmp_path)
    assert book.cash == 5 and book.list_codes() == ["A"] and book.positions[0].cost == 2.5
    with pytest.raises(ValueError):
        Position(code="A", shares=0, cost=1)
    assert Position(code="A", shares=1, cost=-2.5).cost == -2.5


# TC-HRB-006
def test_tc_hrb_006_paid_back_cost(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    book = PositionsBook(as_of=DAY, cash=0.0, positions=[Position(code=A, shares=100, cost=-2.0)])
    pos = _build_builder(lake, book).build(DAY)["positions"][0]
    assert pos["pnl"] == pytest.approx(100 * (10 + 2.0)) and pos["pnl_pct"] is None


# TC-PB-002
def test_tc_pb_002_missing_and_invalid(tmp_path: Path) -> None:
    assert PositionsBook.load(tmp_path).positions == []
    (tmp_path / "config").mkdir()
    path = tmp_path / "config" / "local.positions.yaml"
    path.write_text(
        "positions:\n  - {code: A, shares: 1, cost: 1}\n  - {code: A, shares: 2, cost: 1}\n"
    )
    with pytest.raises(ConfigError):
        PositionsBook.load(tmp_path)
    path.write_text("positions: [unclosed\n")
    with pytest.raises(ConfigError):
        PositionsBook.load(tmp_path)


# TC-PB-003
def test_tc_pb_003_notes_and_rules(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    path = tmp_path / "config" / "local.positions.yaml"
    path.write_text(
        "positions:\n  - {code: A, shares: 1, cost: 1}\n"
        "realized: [{code: Z, pnl: 3}]\n"
        "rules: {max_weight: 0.25, weight_exceptions: [A], review_every_days: 14}\n"
        "notes:\n  A: {thesis: t, stop: 0.9, reviewed: '20261112', conditions:\n"
        "    [{label: g, kind: statement, metric: gm_q, op: '>=', value: 0.22}]}\n"
        "closed:\n  Z: {thesis: sold}\n",
        encoding="utf-8",
    )
    book = PositionsBook.load(tmp_path)
    assert book.rules.max_weight == 0.25 and book.rules.weight_exceptions == ["A"]
    assert book.notes["A"].stop == 0.9 and book.notes["A"].conditions[0].metric == "gm_q"
    assert book.closed["Z"].thesis == "sold"
    path.write_text("positions:\n  - {code: A, shares: 1, cost: 1}\nnotes:\n  Z: {thesis: x}\n")
    with pytest.raises(ConfigError):
        PositionsBook.load(tmp_path)
    path.write_text("positions:\n  - {code: A, shares: 1, cost: 1}\n")
    assert PositionsBook.load(tmp_path).rules.max_weight == 0.20


class FakeReviewer:
    """Stands in for PositionReviewer: records the priced positions it was given."""

    def __init__(self) -> None:
        self.seen: list[str] = []

    def build(self, held: pd.DataFrame, as_of: str) -> dict[str, dict[str, str]]:
        self.seen = list(held["code"])
        return {c: {"as_of": as_of} for c in held["code"]}


# TC-HRB-005
def test_tc_hrb_005_reviews(lake: MiniLake, config: Config, doc: dict) -> None:
    assert doc["reviews"] == {}
    reviewer = FakeReviewer()
    builder = HoldingsRiskBuilder(
        BOOK,
        lake.query,
        FixedModel("m"),
        RiskDecomposer(),
        HoldingsHistoryWriter(lake.query, lake.writer),
        "000300.SH",
        reviewer,  # type: ignore[arg-type]
    )
    reviews = builder.build("20261112")["reviews"]
    assert sorted(reviews) == sorted([A, B, C]) and GONE not in reviewer.seen
    assert reviews[A] == {"as_of": DAY}


ETF, LOOSE = "512100.SH", "510300.SH"


def _write_funds(lake: MiniLake, config: Config) -> None:
    w = SampleFactorLake.write
    closes = [(ETF, 2.0), (LOOSE, 4.0)]
    w(
        lake,
        config,
        "fund_daily",
        [{"ts_code": c, "trade_date": DAY, "close": v} for c, v in closes],
    )
    bench = [("000300.SH", A, 50.0), ("000300.SH", B, 50.0)]
    basket = [("000852.SH", B, 30.0), ("000852.SH", C, 10.0), ("000852.SH", GONE, 20.0)]
    rows = [
        {"index_code": i, "con_code": c, "trade_date": DAY, "weight": v}
        for i, c, v in bench + basket
    ]
    w(lake, config, "index_weight", rows)


# TC-HRB-007
def test_tc_hrb_007_etf_look_through(lake: MiniLake, config: Config) -> None:
    etf, loose = ETF, LOOSE
    _write(lake, config)
    _write_funds(lake, config)
    book = PositionsBook(
        as_of=DAY,
        cash=1000.0,
        positions=[
            Position(code=A, shares=100, cost=8.0),
            Position(code=etf, shares=500, cost=2.1, tracks="000852.SH"),
            Position(code=loose, shares=10, cost=4.0),
        ],
    )
    reviewer = FakeReviewer()
    doc = HoldingsRiskBuilder(
        book,
        lake.query,
        FixedModel("m"),
        RiskDecomposer(),
        HoldingsHistoryWriter(lake.query, lake.writer),
        "000300.SH",
        reviewer,  # type: ignore[arg-type]
    ).build(DAY)
    value = 1000 + 1000 + 40 + 1000.0
    pos = {p["code"]: p for p in doc["positions"]}
    assert (pos[etf]["kind"], pos[etf]["close"], pos[A]["kind"]) == ("etf", 2.0, "stock")
    assert pos[etf]["pnl"] == pytest.approx(500 * (2.0 - 2.1))
    h = pd.Series({A: 1000 / value, B: 0.75 * 1000 / value, C: 0.25 * 1000 / value})
    factor, spec = RiskSnapshot(DAY, X, COV, SPEC).compute_variance(h)
    assert doc["risk"]["total"] == pytest.approx(math.sqrt((factor + spec) * 252), abs=1e-6)
    assert pos[A]["contrib"] + pos[etf]["contrib"] == pytest.approx(1.0, abs=1e-5)
    assert doc["missing"] == [loose] and doc["correlation"]["codes"] == [A, etf]
    rows = {r["code"]: r for r in doc["stock_exposures"]["rows"]}
    assert rows[etf]["industry"] == "ETF"
    assert rows[etf]["values"] == pytest.approx([-0.75])
    assert etf not in reviewer.seen and A in reviewer.seen


# TC-PB-004
def test_tc_pb_004_tracks_optional() -> None:
    assert Position(code="A", shares=1, cost=1).tracks is None
    assert Position(code="E", shares=1, cost=1, tracks="000852.SH").tracks == "000852.SH"
