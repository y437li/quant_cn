"""Plan 21 ph2 check: RetailGaugeFeatureBuilder rows for 2026-11-12 vs the v5 prototype panel
(meta/runs/holder_nowcast holders_v3_feats / holders_v4_flow / holders_v5_feats, q = 20261112, chips from
cyq_qe 20261112 vs 20260930), 20 sampled stocks: max abs difference per feature."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from quant_cn.calculation.holder_count_panel import HolderCountPanel
from quant_cn.calculation.retail_gauge_feature_builder import RetailGaugeFeatureBuilder
from quant_cn.core.config import Config
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.dated_table_writer import DatedTableWriter
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.lake.parquet_writer import ParquetWriter

REPO = Path(__file__).resolve().parents[3]
S = Path("/Volumes/Treasury/quant_cn_lake/meta/runs/holder_nowcast")
OUT = Path("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261118_retail_gauge_port")


def main() -> None:
    cfg = Config.load(REPO)
    query = LakeQuery(LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True))
    builder = RetailGaugeFeatureBuilder(
        RetailGaugeSettings.load(REPO), query, HolderCountPanel(query), DatedTableWriter(query, ParquetWriter(cfg.lake.root))
    )
    new = builder.build(["20261112"]).set_index("ts_code")
    old = (
        pd.read_parquet(S / "holders_v3_feats.parquet")
        .merge(pd.read_parquet(S / "holders_v4_flow.parquet"), on=["ts_code", "q"], how="left")
        .merge(pd.read_parquet(S / "holders_v5_feats.parquet"), on=["ts_code", "q"], how="left")
    )
    old = old[old.q == "20261112"].set_index("ts_code")
    sample = new.index.intersection(old.index).to_series().sample(20, random_state=0).index
    feats = [c for c in old.columns if c != "q" and c in new.columns]
    diff = (new.loc[sample, feats].astype(float) - old.loc[sample, feats].astype(float)).abs().max()
    print("features compared", len(feats), "of", len(new.columns) - 3, "; max abs diff", f"{diff.max():.2e}")
    print(diff[diff > 1e-9].sort_values(ascending=False).head(20).to_string())
    missing = [c for c in new.columns if c not in old.columns]
    print("not in the prototype panel (chip / lags / labels):", missing)
    print("rows", len(new), "features", len(new.columns) - 3)
    OUT.mkdir(parents=True, exist_ok=True)
    diff.rename("max_abs_diff").to_frame().to_csv(OUT / "feature_match.csv")


if __name__ == "__main__" and len(__import__("sys").argv) == 1:
    main()


def match_vintage() -> None:
    """Same check with the lake as it was when the prototype ran (2026-11-12 evening, US time):
    moneyflow for 20261112 and margin_detail for 20261111 / 20261112 were downloaded on 11-13."""
    import quant_cn.calculation.retail_gauge_feature_builder as fb

    fb._MATRIX_SQL = {
        k: (f"SELECT * FROM ({v} WHERE trade_date < '20261112')" if k in ("lg", "elg", "sm") else
            f"SELECT * FROM ({v} WHERE trade_date < '20261111')" if k == "rz" else v)
        for k, v in fb._MATRIX_SQL.items()
    }
    main()




def match_chips() -> None:
    """Chip features vs the prototype formula on its own snapshot file (cyq_qe.parquet, 20261112 vs 20260930)."""
    cfg = Config.load(REPO)
    query = LakeQuery(LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True))
    builder = RetailGaugeFeatureBuilder(
        RetailGaugeSettings.load(REPO), query, HolderCountPanel(query), DatedTableWriter(query, ParquetWriter(cfg.lake.root))
    )
    new = builder.build(["20261112"]).set_index("ts_code")
    cyq = pd.read_parquet(S / "cyq_qe.parquet")
    cyq["conc"] = (cyq.cost_85pct - cyq.cost_15pct) / cyq.cost_50pct
    px = query.sql("SELECT ts_code, trade_date, close FROM curated.daily WHERE trade_date IN ('20261112', '20260930')")
    cb, ca = (cyq[cyq.trade_date == d].set_index("ts_code") for d in ("20261112", "20260930"))
    pb, pa = (px[px.trade_date == d].set_index("ts_code").close for d in ("20261112", "20260930"))
    old = pd.DataFrame({"win_b": cb.winner_rate, "conc_b": cb.conc, "pc50_b": np.log(pb / cb.cost_50pct)})
    old["dwin"] = cb.winner_rate - ca.winner_rate
    old["dconc"] = cb.conc - ca.conc
    old["dpc50"] = old.pc50_b - np.log(pa / ca.cost_50pct)
    old["wavg_gap"] = np.log(cb.weight_avg / ca.weight_avg)
    common = new.index.intersection(old.index)
    diff = (new.loc[common, old.columns].astype(float) - old.loc[common].astype(float)).abs().max()
    print("chip features, stocks", len(common), "max abs diff", diff.to_dict())


if __name__ == "__main__" and len(__import__("sys").argv) > 1:
    {"vintage": match_vintage, "chips": match_chips}[__import__("sys").argv[1]]()
