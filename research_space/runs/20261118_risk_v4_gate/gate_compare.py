"""Plan 37 ph2 gate: cne5_v4 (analyst EPFWD / EGRSF / EGRLF) vs cne5_v3_dy from their validation reports
(derived/reports/risk_<name>/validation.parquet): median adjusted R² (whole history, last year), random
portfolios in band and median bias, CSI 300 / 500 / 1000 bias, earnings_yield and growth factor bias;
plus the share of days with |t| > 2 for those two factors' returns (derived.risk_factor_return, the
fitted model). Usage: gate_compare.py [candidate] [current]."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

REPO = Path(__file__).resolve().parents[3]


def read(root: Path, name: str) -> pd.Series:
    v = pd.read_parquet(root / f"derived/reports/risk_{name}/validation.parquet")
    pick = {
        "adj R² (all)": ("median_adj_r2", "model"), "adj R² (last year)": ("median_adj_r2", "window"),
        "random in band": ("share_in_band", "random_portfolios"), "random median bias": ("median_bias", "random_portfolios"),
        "CSI 300 bias": ("bias", "000300.SH"), "CSI 500 bias": ("bias", "000905.SH"), "CSI 1000 bias": ("bias", "000852.SH"),
        "EY factor bias": ("bias", "factor:earnings_yield"), "growth factor bias": ("bias", "factor:growth"),
    }  # fmt: skip
    out = {}
    for label, (metric, scope) in pick.items():
        hit = v[(v["metric"] == metric) & (v["scope"] == scope)]["value"]
        out[label] = round(float(hit.iloc[0]), 4) if len(hit) else None
    return pd.Series(out, name=name)


def main() -> None:
    cand, cur = (sys.argv[1:3] + ["cne5_v4", "cne5_v3_dy"][len(sys.argv[1:3]):])[:2]
    cfg = Config.load(REPO)
    root = Path(cfg.lake.root)
    print(pd.concat([read(root, cur), read(root, cand)], axis=1).to_string())
    cat = LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True)
    fr = LakeQuery(cat).sql("SELECT * FROM derived.risk_factor_return WHERE factor IN ('earnings_yield', 'growth') LIMIT 5")
    print("\nrisk_factor_return columns:", fr.columns.tolist())
    if "t" in fr.columns or "t_stat" in fr.columns:
        col = "t" if "t" in fr.columns else "t_stat"
        s = LakeQuery(cat).sql(f"SELECT factor, avg(CASE WHEN abs({col}) > 2 THEN 1 ELSE 0 END) AS share_t2, count(*) AS n_days "
                               "FROM derived.risk_factor_return WHERE factor IN ('earnings_yield', 'growth') GROUP BY 1")
        print(f"share of days with |t| > 2 ({cand}):\n", s.to_string(index=False))
    cat.close()


if __name__ == "__main__":
    main()
