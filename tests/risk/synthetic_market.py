"""A synthetic market with a known factor structure (RISK_MODEL_DESIGN §6) for risk tests."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

STYLES = ["size", "beta"]


@dataclass
class SyntheticFactorMarket:
    """Country + industries + two styles; planted factor returns and specific vols.

    Industry factor returns satisfy the cap-weighted constraint, so the constrained regression
    should recover them exactly up to noise.
    """

    n_stocks: int = 300
    n_days: int = 260
    n_ind: int = 5
    seed: int = 7
    noise: float = 1.0  # multiplier on specific vols
    days: list[str] = field(init=False)
    codes: list[str] = field(init=False)
    industry: np.ndarray = field(init=False)
    cap: np.ndarray = field(init=False)
    styles: np.ndarray = field(init=False)
    spec_vol: np.ndarray = field(init=False)
    factor_ret: pd.DataFrame = field(init=False)
    returns: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        rng = np.random.default_rng(self.seed)
        self.days = pd.bdate_range("2024-01-02", periods=self.n_days).strftime("%Y%m%d").tolist()
        self.codes = [f"{i:06d}.SZ" for i in range(self.n_stocks)]
        self.industry = np.arange(self.n_stocks) % self.n_ind
        self.cap = np.exp(rng.normal(22.0, 1.0, self.n_stocks))
        self.styles = rng.standard_normal((self.n_stocks, len(STYLES)))
        self.spec_vol = rng.uniform(0.01, 0.03, self.n_stocks) * self.noise
        share = np.array([self.cap[self.industry == i].sum() for i in range(self.n_ind)])
        share = share / share.sum()
        ind = rng.normal(0.0, 0.006, (self.n_days, self.n_ind))
        ind -= np.outer(ind @ share, np.ones(self.n_ind))  # cap-weighted sum 0
        country = rng.normal(0.0, 0.012, self.n_days)
        style = rng.normal(0.0, 0.004, (self.n_days, len(STYLES)))
        names = ["country", *[f"ind_I{i}" for i in range(self.n_ind)], *STYLES]
        planted = np.hstack([country[:, None], ind, style])
        self.factor_ret = pd.DataFrame(planted, index=self.days, columns=names)
        dummies = np.eye(self.n_ind)[self.industry]
        x = np.hstack([np.ones((self.n_stocks, 1)), dummies, self.styles])
        noise = rng.standard_normal((self.n_days, self.n_stocks)) * self.spec_vol
        self.returns = planted @ x.T + noise

    def build_panel(self) -> pd.DataFrame:
        """Regression panel: trade_date, ts_code, ret, circ_mv, l1_code, styles."""
        frames = []
        for t, day in enumerate(self.days):
            frame = pd.DataFrame(
                {
                    "trade_date": day,
                    "ts_code": self.codes,
                    "ret": self.returns[t],
                    "circ_mv": self.cap,
                    "l1_code": [f"I{i}" for i in self.industry],
                }
            )
            for k, name in enumerate(STYLES):
                frame[name] = self.styles[:, k]
            frames.append(frame)
        return pd.concat(frames, ignore_index=True)

    def build_exposures(self) -> pd.DataFrame:
        """RISK_EXPOSURE-shaped rows for every day (styles and industries)."""
        rows = []
        for day in self.days:
            for k, name in enumerate(STYLES):
                rows.append(
                    pd.DataFrame(
                        {
                            "trade_date": day,
                            "ts_code": self.codes,
                            "factor": name,
                            "exposure": self.styles[:, k],
                            "exposure_raw": self.styles[:, k],
                            "is_filled": 0.0,
                        }
                    )
                )
            rows.append(
                pd.DataFrame(
                    {
                        "trade_date": day,
                        "ts_code": self.codes,
                        "factor": [f"ind_I{i}" for i in self.industry],
                        "exposure": 1.0,
                        "exposure_raw": 1.0,
                        "is_filled": 0.0,
                    }
                )
            )
        return pd.concat(rows, ignore_index=True)
