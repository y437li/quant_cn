"""Paper book of the ETF CTA targets: drift, no-trade band, costs (plan 27)."""

from __future__ import annotations

import numpy as np
import pandas as pd


class EtfCtaPaperBook:
    """
    Purpose:
        Follow weekly target weights with a paper account: holdings drift with daily returns;
        after the close of each decision date the ETFs of a group are traded to their targets
        only when the group total or one of its ETFs is off target by band or more ("2点不动");
        an ETF whose target is 0 is always sold; cash absorbs the trades and earns the cash
        return; each trade costs `cost` x its size. Starts all in cash.

    Contract:
        Input:
            band: float >= 0  -- no-trade band in weight points (0.02)
            cost: float >= 0  -- cost per unit traded (0.0015)
            groups: dict[str, str] | None  -- ts_code -> group; a code not listed is its own group
        Output:
            instance; `run(returns, cash, targets, start, no_add)` -> dict of
                nav:      Series   -- account value by session from start (1.0 before trades)
                weights:  DataFrame -- held weights after each session's trades (codes + cash)
                trades:   DataFrame -- traded weight per decision date and code (signed)
        Raises:
            ValueError  -- band or cost < 0; start after the last session

    Used by:
        portfolio.EtfCtaBook  -- back-test record and paper book

    Test cases:
        TC-ECP-001  a target change below the band is not traded; at the band it is
        TC-ECP-007  small ETF targets are bought when their group total reaches the band
        TC-ECP-002  a zero target sells a holding smaller than the band
        TC-ECP-003  costs reduce the NAV by cost x traded weight
        TC-ECP-004  holdings drift with returns between decisions; cash earns its return
        TC-ECP-005  bad band / cost or a start after the data raise ValueError
        TC-ECP-006  a no_add code is not bought on that date but may be sold
    """

    def __init__(self, band: float, cost: float, groups: dict[str, str] | None = None) -> None:
        if band < 0 or cost < 0:
            raise ValueError(f"band and cost must be >= 0: {band}, {cost}")
        self._band = band
        self._cost = cost
        self._groups = groups or {}

    def run(
        self,
        returns: pd.DataFrame,
        cash: pd.Series,
        targets: pd.DataFrame,
        start: pd.Timestamp,
        no_add: dict[pd.Timestamp, list[str]] | None = None,
    ) -> dict[str, pd.DataFrame | pd.Series]:
        """
        Purpose:
            Run the account from `start` to the last session.

        Contract:
            Input:
                returns: DataFrame  -- sessions x codes (NaN = no price, treated as 0 return)
                cash:    Series     -- daily cash return by session
                targets: DataFrame  -- decision dates x codes (subset of returns' columns)
                start:   Timestamp  -- first session of the account
                no_add:  dict | None -- decision date -> codes that may not be increased (premium)
            Output:
                dict  -- see class contract
            Raises:
                ValueError  -- start after the last session
        """
        idx = returns.index[returns.index >= start]
        if idx.empty:
            raise ValueError(f"start {start.date()} is after the last session")
        codes = list(targets.columns)
        r = returns.loc[idx, codes].fillna(0.0).to_numpy()
        c = cash.reindex(idx).fillna(0.0).to_numpy()
        tgt = targets.loc[targets.index >= start]
        label = np.array([self._groups.get(c_, c_) for c_ in codes])
        held, money, blocked = np.zeros(len(codes)), 1.0, no_add or {}
        navs, rows, trades = [], [], {}
        for i, day in enumerate(idx):
            held, money = held * (1.0 + r[i]), money * (1.0 + c[i])
            if day in tgt.index:
                nav = held.sum() + money
                stop = np.array([c_ in blocked.get(day, []) for c_ in codes], dtype=bool)
                goal = tgt.loc[day].to_numpy(dtype=float)
                trade = self._compute_trade(held / nav, goal, stop, label) * nav
                held = held + trade
                money = money - trade.sum() - self._cost * np.abs(trade).sum()
                trades[day] = trade / nav
            nav = held.sum() + money
            navs.append(nav)
            rows.append(np.append(held, money) / nav)
        weights = pd.DataFrame(rows, index=idx, columns=[*codes, "cash"])
        traded = pd.DataFrame.from_dict(trades, orient="index", columns=codes)
        return {"nav": pd.Series(navs, index=idx), "weights": weights, "trades": traded}

    def _compute_trade(
        self, held: np.ndarray, target: np.ndarray, stop: np.ndarray, label: np.ndarray
    ) -> np.ndarray:
        diff = target - held
        off = np.abs(diff) >= self._band - 1e-12
        move = (target <= 0) & (held > 0)
        for g in np.unique(label):
            part = label == g
            if off[part].any() or abs(diff[part].sum()) >= self._band - 1e-12:
                move = move | part
        trade = np.where(move, diff, 0.0)
        return np.where(stop & (trade > 0), 0.0, trade)
