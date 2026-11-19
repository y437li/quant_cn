"""What-if: add 601888.SH to the book (funded from cash) and compare exposures and risk."""
import pandas as pd
from quant_cn.core.config import Config
from quant_cn.core.positions_book import PositionsBook
from quant_cn.lake.lake_catalog import LakeCatalog
from quant_cn.lake.lake_query import LakeQuery
from quant_cn.risk.risk_decomposer import RiskDecomposer
from quant_cn.risk.risk_model_factory import RiskModelFactory
C="601888.SH"; S="20261112"; ANN=252**0.5
cfg=Config.load(); book=PositionsBook.load(cfg.repo_root)
cat=LakeCatalog(cfg.lake.root, cfg.datasets, read_only=True); q=LakeQuery(cat)
model=RiskModelFactory(q).build(cfg.risk_model); snap=model.load_snapshot(S)
codes=[p.code for p in book.positions]+[C]
px=q.sql("select ts_code, close from curated.daily where trade_date=? and list_contains(?, ts_code)",[S,codes]).set_index("ts_code").close
val=pd.Series({p.code:p.shares*px[p.code] for p in book.positions}); total=val.sum()+book.cash
w0=val/total
x=snap.exposures if hasattr(snap,"exposures") else None
dec=RiskDecomposer()
def run(w):
    r=dec.compute(snap,w,"b",None).set_index("component")
    return r
base=run(w0)
ex=snap.exposures
row=ex.loc[C] if C in getattr(ex,"index",[]) else None
styles=["beta","momentum","usd_sensitivity","size","non_linear_size","earnings_yield","book_to_price","dividend_yield","growth","leverage","liquidity","residual_volatility","cash_flow_yield","us_sensitivity"]
inds=[c for c in ex.columns if c.startswith("ind_") and abs(row[c])>1e-9]
print("CDF industry:", {c:round(float(row[c]),2) for c in inds})
print("CDF styles:", {s:round(float(row[s]),2) for s in styles})
print("CDF vol", float(snap.compute_stock_cov([C]).iloc[0,0])**0.5*ANN)
out=[]
for wt in (0,0.03,0.05,0.08):
    w=w0.copy(); w[C]=wt
    r=run(w); risk=r["risk"].astype(float)
    out.append({"中免权重":wt,"总波动":risk["total"]*ANN,"动量":risk["x:momentum"],"美元":risk["x:usd_sensitivity"],"贝塔":risk["x:beta"],"盈利收益率":risk["x:earnings_yield"],"商贸零售":risk.get("x:ind_801200.SI",0)})
print(pd.DataFrame(out).round(3).to_string(index=False))
c=pd.Series({k:float(snap.compute_stock_cov([k,C]).iloc[0,1]/ (snap.compute_stock_cov([k]).iloc[0,0]*snap.compute_stock_cov([C]).iloc[0,0])**0.5) for k in w0.index})
print("corr with holdings:", c.round(2).sort_values().to_dict())
cat.close()
