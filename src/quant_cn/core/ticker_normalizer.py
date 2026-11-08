"""The only place that converts other ticker spellings to Tushare `ts_code` (CODING_STANDARD §4)."""

from __future__ import annotations

import re

_TS_CODE = re.compile(r"^\d{6}\.(SH|SZ|BJ)$")
_CODE_LEN = 6
_PREFIXED = re.compile(r"^(sh|sz|bj)(\d{6})$", re.IGNORECASE)


class TickerNormalizer:
    """
    Purpose:
        Turn common A-share ticker spellings into Tushare `ts_code` and check `ts_code` validity.

    Contract:
        Input:
            code: str  -- "600519.SH", "sh600519", "SZ000001" or a bare 6-digit code
        Output:
            str  -- "NNNNNN.SH" | "NNNNNN.SZ" | "NNNNNN.BJ"
        Raises:
            ValueError  -- unrecognised format or a bare code whose exchange cannot be inferred

    Used by:
        (none yet)

    Test cases:
        TC-TN-001  ts_code passes through unchanged
        TC-TN-002  exchange-prefixed spellings normalised
        TC-TN-003  bare codes inferred by leading digits (6/9 SH, 0/2/3 SZ, 4/8 BJ)
        TC-TN-004  garbage raises ValueError; is_valid is False for it
    """

    def normalize(self, code: str) -> str:
        """
        Purpose:
            Convert `code` to `ts_code`.

        Contract:
            Input:
                code: str  -- see class contract
            Output:
                str  -- ts_code
            Raises:
                ValueError  -- unrecognised format
        """
        text = code.strip()
        if _TS_CODE.match(text.upper()):
            return text.upper()
        prefixed = _PREFIXED.match(text)
        if prefixed:
            return f"{prefixed.group(2)}.{prefixed.group(1).upper()}"
        if len(text) == _CODE_LEN and text.isdigit():
            return f"{text}.{self._get_exchange(text)}"
        raise ValueError(f"unrecognised ticker {code!r}")

    def is_valid(self, code: str) -> bool:
        """
        Purpose:
            True if `code` is already a well-formed `ts_code`.

        Contract:
            Input:
                code: str
            Output:
                bool
            Raises:
                (none)
        """
        return bool(_TS_CODE.match(code))

    def _get_exchange(self, digits: str) -> str:
        head = digits[0]
        if head in "69":
            return "SH"
        if head in "023":
            return "SZ"
        if head in "48":
            return "BJ"
        raise ValueError(f"cannot infer exchange for {digits!r}")
