"""Rank cyclical L3 industries from the 20261116_cycle_screen output: (A) cheap with TTM profit near peak,
(B) cheap-ish with two quarters of y/y profit growth. Reads cycle_l3.csv; prints both lists."""
from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config

pd.set_option("display.width", 250)
L = Path(Config.load(Path(".")).lake.root) / "meta/runs/research/20261116_cycle_screen"
d = pd.read_csv(L / "cycle_l3.csv")
d = d[(d.mv_yi >= 300) & (d.ttm_yi > 0)]
d["turn"] = (d.yoy_q2 > 0.15) & (d.yoy_q3 > 0.15)
cols = ["l1", "ind", "n", "mv_yi", "ttm_yi", "ttm_vs_peak", "yoy_q1", "yoy_q2", "yoy_q3", "pb", "pb_pct"]
print("A: cheap with profit near peak"); print(d[(d.pb_pct <= 0.15) & (d.ttm_vs_peak >= 0.7)].sort_values("pb_pct")[cols].to_string(index=False))
print("B: turning and cheap-ish"); print(d[(d.pb_pct <= 0.35) & d.turn].sort_values("yoy_q3", ascending=False)[cols].to_string(index=False))
