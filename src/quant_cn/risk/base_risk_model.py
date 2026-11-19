"""The risk-model extension point (RISK_MODEL_DESIGN §2, D-045)."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from quant_cn.risk.risk_snapshot import RiskSnapshot


class BaseRiskModel(ABC):
    """
    Purpose:
        Abstract risk model: produces the RISK_EXPOSURE / FACTOR_RETURN / FACTOR_COV /
        SPECIFIC_RISK frames for a pipeline step and answers portfolio-risk questions for a
        session from those frames. A statistical (PCA) model would be another subclass (D-045).

    Contract:
        Input:
            name: str  -- model id (config `risk_model.name`)
        Output:
            instance; `load_snapshot(date)`, `compute_portfolio_risk(weights, date)`
        Raises:
            TypeError  -- when instantiated directly

    Used by:
        portfolio.OpportunityScreen  -- snapshot for the fit rule
        risk.RiskModel  -- subclass
        risk.RiskModelValidator  -- injected type or call
        portfolio.HoldingsRiskBuilder  -- injected type or call

    Test cases:
        TC-BRM-001  compute_portfolio_risk = sqrt(factor + specific variance) of the snapshot;
                    the base cannot be instantiated
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def load_snapshot(self, trade_date: str) -> RiskSnapshot:
        """
        Purpose:
            The fitted model as of a session.

        Contract:
            Input:
                trade_date: str  -- YYYYMMDD session with stored frames
            Output:
                RiskSnapshot
            Raises:
                LakeError  -- frames missing for the session
        """

    def compute_portfolio_risk(self, weights: pd.Series, trade_date: str) -> float:
        """
        Purpose:
            Forecast daily volatility of a portfolio held from the close of `trade_date`.

        Contract:
            Input:
                weights: Series     -- index ts_code, weights (any sign; uncovered names ignored)
                trade_date: str     -- YYYYMMDD
            Output:
                float  -- sqrt(h'XFX'h + h'Dh) >= 0, daily units
            Raises:
                LakeError  -- frames missing
        """
        factor, specific = self.load_snapshot(trade_date).compute_variance(weights)
        return float((factor + specific) ** 0.5)
