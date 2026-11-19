"""Append the plan 36 research variants of the pricing gap to the campaign TrialLog (meta/trials),
so the multiple-testing count includes them (FACTOR_TESTING_DESIGN §6; plan 25 precedent).
Idempotent: a variant already logged (TrialLog.find_trial) is skipped."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.statistic.trial_log import TrialLog

REPO = Path(__file__).resolve().parents[3]
FACTOR = "pricing_gap_research"
# (params, horizon, Sharpe per period or None, mean IC) from RESEARCH_LOG rows 20261118_linear_pricing_gap*
VARIANTS = [
    ({"fade": 0.7, "exit_pe": 15, "neutral": "none"}, 20, None, -0.0533),
    ({"fade": 0.7, "exit_pe": 15, "neutral": "none"}, 60, None, -0.0534),
    ({"fade": 0.5, "exit_pe": 20, "neutral": "none"}, 20, None, -0.0528),
    ({"fade": 0.5, "exit_pe": 20, "neutral": "none"}, 60, None, -0.0527),
    ({"fade": 0.7, "exit_pe": 15, "neutral": "industry", "weight": "equal"}, 20, 1.12 / 12**0.5, None),
    ({"fade": 0.7, "exit_pe": 15, "neutral": "industry_size", "weight": "equal"}, 20, 1.01 / 12**0.5, None),
    ({"fade": 0.7, "exit_pe": 15, "neutral": "none", "weight": "equal"}, 20, 0.64 / 12**0.5, None),
    ({"fade": 0.7, "exit_pe": 15, "neutral": "none", "weight": "cap"}, 20, 0.25 / 12**0.5, None),
    ({"fade": 0.7, "exit_pe": 15, "neutral": "industry", "weight": "cap"}, 20, 0.37 / 12**0.5, None),
    ({"fade": 0.7, "exit_pe": 15, "neutral": "industry_size", "weight": "cap"}, 20, 0.42 / 12**0.5, None),
    ({"family": "second_condition_rules", "tests": 40}, 20, None, None),
    ({"family": "revision_filter"}, 20, 1.10 / 12**0.5, None),
]


def main() -> None:
    cfg = Config.load(REPO)
    path = Path(cfg.lake.root) / "meta" / "trials" / f"{cfg.campaign.id}.parquet"
    log = TrialLog.from_frame(cfg.campaign.id, pd.read_parquet(path))
    before = log.n_trials
    for params, horizon, sr, ic in VARIANTS:
        if log.find_trial(FACTOR, params, horizon) is None:
            log.add_trial(FACTOR, params, horizon, sr, ic)
    log.build_frame().to_parquet(path)
    print(f"trials {before} -> {log.n_trials}")


if __name__ == "__main__":
    main()
