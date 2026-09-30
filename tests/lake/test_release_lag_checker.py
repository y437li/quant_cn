from __future__ import annotations

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.compactor import Compactor
from quant_cn.lake.release_lag_checker import ReleaseLagChecker
from tests.support import MiniLake


def write_releases(lake: MiniLake, config: Config, dates: list[str]) -> None:
    spec = config.get_dataset("macro_release_cpi")
    rows = [
        {"series": "cpi", "release_date": d, "actual": 1.0, "forecast": None, "previous": None}
        for d in dates
    ]
    lake.writer.write_raw(spec, "all", pd.DataFrame(rows))
    Compactor(lake.catalog, lake.query, lake.writer, lake.clock).rebuild(spec)


# TC-RLC-001
def test_tc_rlc_001_later_than_rule(lake: MiniLake, config: Config) -> None:
    # Dec-2024 print on 01-10 (lag 10), Jan-2025 print on 02-21 (lag 21 > rule 20), a 1st-of-month
    # placeholder and a pre-2010 row are ignored
    write_releases(lake, config, ["20250110", "20250221", "20250301", "20090115"])
    out = ReleaseLagChecker(lake.query, config.datasets).compute()
    row = out[out["dataset"] == "cn_cpi"].to_dict("records")[0]
    assert row["rule_days"] == 20 and row["releases"] == 2
    assert row["observed_max"] == 21 and row["later_than_rule"] == 1 and row["latest"] == "20250221"


# TC-RLC-002
def test_tc_rlc_002_skipped(lake: MiniLake, config: Config) -> None:
    assert ReleaseLagChecker(lake.query, config.datasets).compute().empty  # no release tables yet


# TC-RLC-003
def test_tc_rlc_003_lines(lake: MiniLake, config: Config) -> None:
    write_releases(lake, config, ["20250110", "20250221"])
    lines = ReleaseLagChecker.build_lines(ReleaseLagChecker(lake.query, config.datasets).compute())
    assert lines == [
        "cn_cpi: rule 20d, observed max 21d over 2 releases"
        " -> WARNING: 1 release(s) later than the rule"
    ]
