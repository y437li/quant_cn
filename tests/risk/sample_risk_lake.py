"""A mini lake with prices, caps, Shenwan membership, statements and a universe (risk tests)."""

from __future__ import annotations

from typing import ClassVar

import numpy as np
import pandas as pd

from quant_cn.core.config import Config, UniverseConfig
from quant_cn.core.date_codec import DateCodec
from quant_cn.core.risk_model_settings import RiskModelSettings, StyleSpec
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.derived_views import DerivedViews
from quant_cn.lake.pit_aligner import PitAligner
from quant_cn.pipeline.universe_step import UniverseStep
from tests.support import MiniLake, Sample, SampleFactorLake


class SampleRiskLake:
    """120 stocks in 3 industries over 150 sessions spanning a year end."""

    DAYS: ClassVar[list[str]] = (
        pd.bdate_range("2025-09-01", periods=150).strftime("%Y%m%d").tolist()
    )
    CODES: ClassVar[list[str]] = [f"{i:06d}.SZ" for i in range(120)]

    @classmethod
    def build_settings(cls) -> RiskModelSettings:
        """Two styles, small simulation counts and windows that fit 150 sessions."""
        return RiskModelSettings(
            name="test",
            start=cls.DAYS[0],
            styles=[
                StyleSpec(name="size", descriptors={"lncap": 1.0}),
                StyleSpec(name="liquidity", descriptors={"stom": 1.0}, orthogonalize_to=["size"]),
            ],
            monitor_styles=[StyleSpec(name="beta_monitor", descriptors={"beta": 1.0})],
            min_regression_names=20,
            eigen_sims=20,
            min_factor_obs=40,
            specific_min_obs=20,
            specific_full_obs=40,
            validation_sessions=21,
            validation_portfolios=5,
            validation_names=10,
            benchmarks=[],
        )

    @classmethod
    def write(cls, lake: MiniLake, config: Config) -> None:
        """Write every dataset, refresh the views, PIT states and the universe."""
        write = SampleFactorLake.write
        lake.writer.write_raw(
            config.get_dataset("trade_cal"), "all", Sample.build_trade_cal(cls.DAYS)
        )
        Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(
            config.get_dataset("trade_cal")
        )
        basic_rows = [
            {"ts_code": c, "list_status": "L", "list_date": "20000101"} for c in cls.CODES
        ]
        write(lake, config, "stock_basic", basic_rows)
        names = [{"ts_code": c, "name": "x", "start_date": "20000101"} for c in cls.CODES]
        write(lake, config, "namechange", names)
        cls.write_market(lake, config)
        cls.write_reference(lake, config)
        views = DerivedViews(lake.catalog, lake.query, config.datasets)
        views.refresh()
        PitAligner(lake.catalog, lake.query, DateCodec()).refresh()
        rules = UniverseConfig(start=cls.DAYS[0], min_sessions=1, exchanges=["SH", "SZ"])
        UniverseStep(lake.query, lake.writer, rules).run("r0")
        views.refresh_tables()

    @classmethod
    def write_market(cls, lake: MiniLake, config: Config) -> None:
        """daily, adj_factor and daily_basic (caps in 10k CNY, turnover in percent)."""
        rng = np.random.default_rng(21)
        cap = np.exp(rng.normal(12, 1, len(cls.CODES)))
        market = rng.normal(0, 0.012, len(cls.DAYS))
        rets = market[:, None] + rng.normal(0, 0.02, (len(cls.DAYS), len(cls.CODES)))
        close = 10 * np.cumprod(1 + rets, axis=0)
        bars, basic, adj = [], [], []
        for t, day in enumerate(cls.DAYS):
            for i, code in enumerate(cls.CODES):
                key = {"ts_code": code, "trade_date": day}
                bars.append(key | {"open": close[t, i], "close": close[t, i]})
                adj.append(key | {"adj_factor": 1.0})
                mv = cap[i] * close[t, i] / 10
                turnover = float(rng.uniform(0.5, 5))
                basic.append(key | {"total_mv": mv, "circ_mv": mv, "turnover_rate_f": turnover})
        SampleFactorLake.write(lake, config, "daily", bars)
        SampleFactorLake.write(lake, config, "adj_factor", adj)
        SampleFactorLake.write(lake, config, "daily_basic", basic)

    @classmethod
    def write_reference(cls, lake: MiniLake, config: Config) -> None:
        """Shenwan membership (3 L1 groups) and one balance-sheet statement."""
        members = [
            {
                "ts_code": c,
                "l1_code": f"80{i % 3}",
                "l1_name": "x",
                "l3_code": f"L3{i % 3}",
                "in_date": "20000101",
            }
            for i, c in enumerate(cls.CODES)
        ]
        SampleFactorLake.write(lake, config, "index_member_all", members)
        stmt = {
            "ts_code": cls.CODES[0],
            "report_type": "1",
            "update_flag": "1",
            "end_date": "20250630",
            "ann_date": "20250820",
            "f_ann_date": "20250820",
            "total_hldr_eqy_exc_min_int": 1e6,
        }
        SampleFactorLake.write(lake, config, "balancesheet_vip", [stmt])
