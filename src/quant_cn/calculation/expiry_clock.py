"""How time to expiry is measured: calendar minutes (CBOE) or trading sessions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

ClockMode = Literal["calendar", "trading"]
MINUTES_PER_DAY = 1440
MINUTES_PER_YEAR = 365 * MINUTES_PER_DAY
SESSIONS_PER_YEAR = 244
TARGET_SESSIONS = 21


class ExpiryClock:
    """
    Purpose:
        Convert (trade_date, expiry) to the time units the VIX formulas use. "calendar" is the
        CBOE white paper: minutes, 30-day target, 365-day year. "trading" counts exchange sessions
        after the trade date up to expiry: 21-session target, 244-session year, so holidays inside
        a term add no time (the Mid-Autumn / National Day roll artefact disappears).

    Contract:
        Input:
            mode:     "calendar" | "trading"
            sessions: Sequence[str]  -- open trading days (YYYYMMDD), must cover every expiry used
                                        in "trading" mode; ignored in "calendar" mode
        Output:
            instance; `get_units`, `get_target`, `get_year`
        Raises:
            ValueError  -- trading mode without sessions

    Used by:
        calculation.VixCalculator  -- T, N1, N2, N30, N365 per day

    Test cases:
        TC-EC-001  calendar mode returns minutes; year fraction = days / 365
        TC-EC-002  trading mode counts sessions strictly after the date through expiry
        TC-EC-003  trading mode without sessions, or expiry past the last session, raises ValueError
    """

    def __init__(self, mode: ClockMode = "calendar", sessions: Sequence[str] = ()) -> None:
        if mode == "trading" and not sessions:
            raise ValueError("trading clock needs the trading sessions")
        self.mode = mode
        self._sessions = sorted(sessions)

    def get_units(self, trade_date: str, expiry: str, calendar_days: int) -> float:
        """
        Purpose:
            Time to expiry in the clock's unit (minutes or sessions).

        Contract:
            Input:
                trade_date: str; expiry: str  -- YYYYMMDD
                calendar_days: int            -- expiry minus trade date in days
            Output:
                float > 0
            Raises:
                ValueError  -- trading mode and the expiry lies past the known sessions
        """
        if self.mode == "calendar":
            return float(calendar_days * MINUTES_PER_DAY)
        if not self._sessions or expiry > self._sessions[-1]:
            raise ValueError(f"trading sessions end before expiry {expiry}")
        return float(sum(1 for d in self._sessions if trade_date < d <= expiry))

    def get_target(self) -> float:
        """
        Purpose:
            The constant-maturity target in the clock's unit.

        Contract:
            Input:
                (none)
            Output:
                float  -- 30 days of minutes, or 21 sessions
            Raises:
                (none)
        """
        return float(30 * MINUTES_PER_DAY if self.mode == "calendar" else TARGET_SESSIONS)

    def get_year(self) -> float:
        """
        Purpose:
            One year in the clock's unit.

        Contract:
            Input:
                (none)
            Output:
                float  -- 525600 minutes, or 244 sessions
            Raises:
                (none)
        """
        return float(MINUTES_PER_YEAR if self.mode == "calendar" else SESSIONS_PER_YEAR)
