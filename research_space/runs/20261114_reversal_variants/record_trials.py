"""Append the plan 25 research variants (run 20261114_reversal_variants, 20-day raw rank IC) to the
campaign TrialLog so the multiple-testing count includes them. Idempotent (TrialLog.find_trial)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.statistic.trial_log import TrialLog

REPO = Path(__file__).resolve().parents[3]
FACTOR = "reversal_research"
VARIANTS = [  # (signal, controls, 20-day rank IC) from reversal_variants_ic.csv
    ("rev_total", "raw", 0.0596),
    ("rev_overnight", "raw", -0.0312),
    ("rev_intraday", "raw", 0.0709),
    ("rev_high_turnover_days", "raw", 0.0711),
    ("rev_low_turnover_days", "raw", -0.0178),
    ("rev_intraday_high_tv", "raw", 0.076),
    ("rev_intraday_high_tv", "net of reversal_1m+size+turnover", 0.045),
]


def main() -> None:
    cfg = Config.load(REPO)
    path = Path(cfg.lake.root) / "meta" / "trials" / f"{cfg.campaign.id}.parquet"
    log = TrialLog.from_frame(cfg.campaign.id, pd.read_parquet(path))
    before = log.n_trials
    for signal, controls, ic in VARIANTS:
        params = {"signal": signal, "controls": controls, "entry": "next open"}
        if log.find_trial(FACTOR, params, 20) is None:
            log.add_trial(FACTOR, params, 20, None, ic)
    log.build_frame().to_parquet(path)
    print(f"trials {before} -> {log.n_trials}")


if __name__ == "__main__":
    main()
