"""FACTOR_TESTING_DESIGN §6 criteria 1-3 for the campaign (plan 36 ph3): FactorAcceptance at 20
sessions on the campaign's IC_TEST, plus the IC / long-short lines of pricing_gap and the score.
Usage: campaign_acceptance.py <ic_test.parquet> [<quantiles.parquet>]."""
from __future__ import annotations

import sys

import pandas as pd

from quant_cn.factor.factor_acceptance import FactorAcceptance


def main() -> None:
    ic_test = pd.read_parquet(sys.argv[1])
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    verdict = FactorAcceptance(horizon=20).compute(ic_test)
    print(verdict.to_string())
    cols = [c for c in ic_test.columns if c in ("factor", "horizon", "window", "ic_mean", "icir", "nw_t", "p_bhy", "p_rw", "ls_sharpe", "ls_mean")]
    sub = ic_test[ic_test["factor"].isin(["pricing_gap", "score", "dividend_yield", "ep_ttm"])]
    print(sub[cols].sort_values(["factor", "horizon"]).to_string())


if __name__ == "__main__":
    main()
