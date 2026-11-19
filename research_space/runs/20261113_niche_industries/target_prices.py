"""Target prices for the niche-industry companies: report_rc max/min_price vs targets extracted from the
report PDFs (meta/runs/valuation/valuations.jsonl, plan 13 ph3), last 12 months; median vs today's close."""
import json
from pathlib import Path

import pandas as pd

from quant_cn.core.config import Config
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery

c = Config.load(Path("."))
LAKE = Path(c.lake.root)
OUT = LAKE / "meta/runs/research/20261113_niche_industries"
cov = pd.read_csv(OUT / "coverage.csv", dtype={"first_report": str})
cov["code6"] = cov["ts_code"].str[:6]
rows = []
for line in (LAKE / "meta/runs/valuation/valuations.jsonl").read_text().splitlines():
    d = json.loads(line)
    if d.get("code") in set(cov["code6"]) and (d.get("date") or "") > "20251113":
        t = d.get("target_price")
        tp = t.get("value") if isinstance(t, dict) else t
        rows.append({"code6": d["code"], "date": d["date"], "org": d.get("org"), "tp": pd.to_numeric(tp, errors="coerce")})
pdf = pd.DataFrame(rows, columns=["code6", "date", "org", "tp"])
cat = LakeCatalog(c.lake.root, c.datasets, read_only=True)
rc = LakeQuery(cat).sql("""SELECT DISTINCT ts_code, report_date, org_name, max_price, min_price FROM curated.report_rc
    WHERE list_contains(?, ts_code) AND report_date > '20251113'""", [cov["ts_code"].tolist()])
cat.close()
rc["tp"] = rc[["max_price", "min_price"]].mean(axis=1)
rc_tp = rc.dropna(subset=["tp"]).groupby("ts_code").agg(rc_n=("tp", "size"), rc_tp=("tp", "median"),
                                                       rc_orgs=("org_name", lambda s: "、".join(sorted(set(s)))))
pdf_tp = pdf.dropna(subset=["tp"]).groupby("code6").agg(pdf_n=("tp", "size"), pdf_tp=("tp", "median"))
pdf_all = pdf.groupby("code6").size().rename("pdf_reports")
df = cov.set_index("ts_code").join(rc_tp).reset_index().set_index("code6").join(pdf_tp).join(pdf_all)
df["tp"] = df["pdf_tp"].fillna(df["rc_tp"])
df["upside"] = ((df["tp"] / df["close"] - 1) * 100).round(0)
pd.set_option("display.width", 220)
cols = ["l3_name", "name", "close", "reports_12m", "pdf_reports", "rc_n", "pdf_n", "rc_tp", "pdf_tp", "upside", "rc_orgs"]
print(f"companies {len(df)}; with any target price {int(df['tp'].notna().sum())}")
print(df[df["tp"].notna()][cols].round(2).to_string(index=False))
df.to_csv(OUT / "target_prices.csv")
