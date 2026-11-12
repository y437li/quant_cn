"""Small in-memory inputs for descriptor and model tests (no lake)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_cn.risk.risk_input_loader import RiskInputs
from tests.risk.synthetic_market import SyntheticFactorMarket


class InputsBuilder:
    """RiskInputs from a SyntheticFactorMarket: prices from its returns, caps, Shenwan codes."""

    @staticmethod
    def build(market: SyntheticFactorMarket, start_index: int = 0) -> RiskInputs:
        close = 10 * np.cumprod(1 + market.returns, axis=0)
        days, codes = market.days, market.codes
        prices = pd.DataFrame(
            {
                "trade_date": np.repeat(days, len(codes)),
                "ts_code": np.tile(codes, len(days)),
                "close_adj": close.ravel(),
            }
        )
        basic = prices[["trade_date", "ts_code"]].assign(
            total_mv=np.tile(market.cap / 1e4, len(days)),
            circ_mv=np.tile(market.cap / 1e4, len(days)),
            turnover_rate_f=1.0,
        )
        inside = days[start_index:]
        members = pd.DataFrame(
            {
                "trade_date": np.repeat(inside, len(codes)),
                "ts_code": np.tile(codes, len(inside)),
                "l1_code": np.tile([f"I{i}" for i in market.industry], len(inside)),
                "industry_backfilled": 0.0,
                "log_mcap": np.tile(np.log(market.cap), len(inside)),
            }
        )
        fundamentals = pd.DataFrame(
            columns=["trade_date", "ts_code", "field", "value", "end_date", "ann_date"]
        )
        annual = pd.DataFrame(columns=["as_of", "ts_code", "end_date", "field", "value"])
        return RiskInputs(inside[0], inside[-1], prices, basic, members, fundamentals, annual)
