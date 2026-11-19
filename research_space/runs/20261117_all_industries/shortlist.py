"""Filter leaders.csv from all_industries.py: no veto (gauge < 0.9), gauge <= 0.3, 2027E PE <= 15,
2027E not cut in 3m, price at or below the chip-cost median. Prints the pass list and near misses."""
from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config

pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
O = Path(Config.load(Path(".")).lake.root) / "meta/runs/research/20261117_all_industries"
L = pd.read_csv(O / "leaders.csv")
L["checks"] = ((L.gauge <= 0.3).astype(int) + (L.pe27 <= 15).astype(int) + (L.rev27_3m >= 0).astype(int) + L.below_cost50.astype(int))
cols = ["bucket", "l3", "name", "mv", "close", "pe27", "rev27_3m", "pb_pct", "gauge", "winner", "cost15", "cost50", "oil_b", "oil_t", "us10y_b", "us10y_t", "checks"]
ok = L[~L.veto].sort_values(["checks", "pe27"], ascending=[False, True])
print("pass 4/4"); print(ok[ok.checks == 4][cols].to_string(index=False))
print("3/4"); print(ok[ok.checks == 3][cols].to_string(index=False))
print("veto"); print(L[L.veto][["l3", "name", "gauge"]].to_string(index=False))
ok.to_csv(O / "shortlist.csv", index=False)
