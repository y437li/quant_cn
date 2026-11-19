"""Contract tests for portfolio.OpportunityScreen (plan 21 ph4)."""

from __future__ import annotations

import pandas as pd
import pytest

from quant_cn.calculation.company_cycle_panel import CompanyCyclePanel
from quant_cn.core.config import Config
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.discovery_settings import DiscoverySettings
from quant_cn.core.exceptions import LakeError
from quant_cn.core.opportunity_settings import OpportunitySettings
from quant_cn.core.positions_book import Position, PositionsBook
from quant_cn.lake.chip_structure_reader import COLUMNS as CHIP_COLUMNS
from quant_cn.lake.chip_structure_reader import ChipStructureReader
from quant_cn.lake.dated_table_store import DatedTableStore
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.statement_version_reader import COLUMNS as VERSION_COLUMNS
from quant_cn.lake.statement_version_reader import StatementVersionReader
from quant_cn.lake.ticker_alias_map import TickerAliasMap
from quant_cn.lake.valuation_history_reader import ValuationHistoryReader
from quant_cn.portfolio.opportunity_rules import OpportunityRules
from quant_cn.portfolio.opportunity_screen import OUTPUT_COLUMNS, OpportunityScreen
from quant_cn.portfolio.style_fit_checker import StyleFitChecker
from quant_cn.risk.base_risk_model import BaseRiskModel
from quant_cn.risk.risk_snapshot import RiskSnapshot
from tests.support import MiniLake, SampleFactorLake

DAY, PREV = "20261113", "20261112"
GOOD, NEAR, HOT, HELD, ST, SMALL, OLD = (f"00000{i}.SZ" for i in range(1, 8))
CODES = [GOOD, NEAR, HOT, HELD, ST, SMALL, OLD]
SETTINGS = OpportunitySettings()
X = pd.DataFrame({"country": 1.0, "momentum": -1.0}, index=CODES)
X.loc[HELD, "momentum"] = 1.0
SPEC = pd.Series(0.02, index=CODES)
BOOK = PositionsBook(
    as_of=DAY, cash=0.0, positions=[Position(code=HELD, name="h", shares=100, cost=1.0)]
)


class FixedModel(BaseRiskModel):
    """One snapshot for every session."""

    def load_snapshot(self, trade_date: str) -> RiskSnapshot:
        cov = pd.DataFrame(0.0, index=X.columns, columns=X.columns)
        return RiskSnapshot(trade_date, X, cov, SPEC)


class FakeChips(ChipStructureReader):
    """Signal rows: every name inflows 4 of 4 weeks except NEAR."""

    def read(self, codes: list[str], as_of: str) -> pd.DataFrame:
        out = pd.DataFrame(0.0, index=pd.Index(codes, name="ts_code"), columns=CHIP_COLUMNS)
        out["lg_weeks_pos_4w"] = [1.0 if c == NEAR else 4.0 for c in codes]
        return out


class FakeVersions(StatementVersionReader):
    """No statements: the panel below supplies the figures."""

    def read_versions(self, fields: object, as_of: str, start: str) -> pd.DataFrame:
        return pd.DataFrame({"ts_code": CODES}).reindex(columns=VERSION_COLUMNS)


class FakeCycle(CompanyCyclePanel):
    """Profit up 50% YoY and 10% QoQ for every name."""

    def build(self, versions: pd.DataFrame, as_of: str) -> pd.DataFrame:
        codes = versions["ts_code"].tolist()
        return pd.DataFrame({"ts_code": codes, "period": "20260930", "np_yoy": 0.5, "np_qoq": 0.1})


class FakeValuations(ValuationHistoryReader):
    """Every name trades at pb 1 against a median of 2."""

    def read(self, codes: list[str], field: str, start: str, as_of: str) -> pd.DataFrame:
        index = pd.Index(codes, name="ts_code")
        return pd.DataFrame({"value": 1.0, "median": 2.0, "n_days": 100.0}, index=index)


def _write(lake: MiniLake, config: Config) -> None:
    w = SampleFactorLake.write
    cap = {c: 600000.0 for c in CODES} | {SMALL: 100000.0}  # 万元: 60亿, SMALL 10亿
    w(lake, config, "daily_basic", [{"ts_code": c, "trade_date": DAY, "circ_mv": v}
                                    for c, v in cap.items()])  # fmt: skip
    names = {c: "x" for c in CODES} | {ST: "*ST x"}
    w(lake, config, "stock_basic", [{"ts_code": c, "name": n} for c, n in names.items()])
    w(lake, config, "daily", [{"ts_code": HELD, "trade_date": DAY, "close": 10.0}])
    gauge = pd.DataFrame(
        {
            "ts_code": CODES, "as_of": DAY, "q": "20261231", "pct": 0.1, "exp_change": -0.05,
            "iqr_lo": -0.1, "iqr_hi": 0.0, "avoid": False, "lo_streak": 3, "hi_streak": 0,
            "retail_leaving": True, "avoid_strong": False, "model_version": "v5",
        }
    )  # fmt: skip
    gauge.loc[gauge["ts_code"] == HOT, ["pct", "avoid"]] = [0.95, True]
    gauge.loc[gauge["ts_code"] == OLD, "as_of"] = "20260901"  # older than 45 days
    for year, rows in gauge.groupby(gauge["as_of"].str[:4]):
        lake.writer.write_derived("retail_gauge", int(str(year)), rows)
    spec = pd.DataFrame({"trade_date": DAY, "ts_code": CODES, "sigma": 0.02, "sigma_raw": 0.0,
                         "method": "x"})  # fmt: skip
    lake.writer.write_derived("risk_specific_risk", 2026, spec)
    DerivedViews(lake.catalog, lake.query, config.datasets).refresh_tables()


def _build(lake: MiniLake, config: Config) -> OpportunityScreen:
    aliases = TickerAliasMap(lake.catalog, lake.query, config.ticker_aliases)
    return OpportunityScreen(
        SETTINGS,
        lake.query,
        FakeChips(lake.query),
        FakeValuations(lake.query),
        FakeVersions(lake.query, aliases, DateCodec()),
        FakeCycle(DateCodec(), DiscoverySettings()),
        FixedModel("m"),
        OpportunityRules(SETTINGS),
        StyleFitChecker(SETTINGS),
        DatedTableStore(lake.writer),
    )


# TC-OSC-001
def test_tc_osc_001_list(lake: MiniLake, config: Config) -> None:
    _write(lake, config)
    screen = _build(lake, config)
    previous = pd.DataFrame({"as_of": [PREV], "ts_code": [GOOD], "status": ["listed"]})
    DatedTableStore(lake.writer).write("opportunity_list", previous, "as_of")
    out = screen.build(DAY, BOOK)
    assert list(out.columns) == OUTPUT_COLUMNS
    assert out["ts_code"].tolist() == [GOOD, NEAR]
    rows = out.set_index("ts_code")
    assert rows.loc[GOOD, "status"] == "listed" and not rows.loc[GOOD, "is_new"]
    assert rows.loc[NEAR, "status"] == "near" and rows.loc[NEAR, "missing"] == "inflow"
    assert rows.loc[NEAR, "is_new"] and rows.loc[GOOD, "fit_styles"] == "momentum"
    assert (out["as_of"] == DAY).all() and rows.loc[GOOD, "circ_mv"] == pytest.approx(60.0)
    screen.write(out)
    stored = DatedTableStore(lake.writer).read("opportunity_list", ["2026"])
    assert sorted(stored["as_of"].unique()) == [PREV, DAY]


# TC-OSC-002
def test_tc_osc_002_missing_inputs(lake: MiniLake, config: Config) -> None:
    with pytest.raises(LakeError):
        _build(lake, config).build(DAY, BOOK)
    SampleFactorLake.write(
        lake, config, "daily_basic", [{"ts_code": GOOD, "trade_date": DAY, "circ_mv": 6e5}]
    )
    with pytest.raises(LakeError, match="retail-gauge"):
        _build(lake, config).build(DAY, BOOK)
