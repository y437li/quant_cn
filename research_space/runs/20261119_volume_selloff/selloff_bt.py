"""中证1000 high-volume selloff days (-3% and turnover >= k x 20d mean): forward returns."""
import duckdb, pandas as pd, numpy as np
L = '/Volumes/Treasury/quant_cn_lake'
c = duckdb.connect()
d = c.sql(f"""select trade_date, close, pct_chg, amount from read_parquet('{L}/raw/index_daily/**/*.parquet', union_by_name=true)
where ts_code='000852.SH' order by trade_date""").df().drop_duplicates('trade_date').set_index('trade_date')
d['amt_ratio'] = d.amount / d.amount.shift(1).rolling(20).mean()
for h in (5, 20, 60):
    d[f'f{h}'] = d.close.shift(-h) / d.close - 1
d['dd250'] = d.close / d.close.rolling(250, min_periods=60).max() - 1
base = d[['f20', 'f60']].mean()
out = []
for drop in (-3, -4):
    for k in (1.0, 1.3, 1.5):
        ev = d[(d.pct_chg <= drop) & (d.amt_ratio >= k)]
        keep, last = [], None
        for t in ev.index:
            i = d.index.get_loc(t)
            if last is None or i - last > 10:
                keep.append(t); last = i
        e = d.loc[keep]
        for cond, sub in (('all', e), ('dd<=-15%', e[e.dd250 <= -0.15])):
            s = sub.dropna(subset=['f60'])
            out.append(dict(drop=drop, k=k, cond=cond, n=len(sub), n60=len(s),
                            f20_mean=sub.f20.mean(), f20_hit=(sub.f20 > 0).mean(),
                            f60_mean=s.f60.mean(), f60_med=s.f60.median(), f60_hit=(s.f60 > 0).mean()))
r = pd.DataFrame(out)
pd.set_option('display.width', 200)
print('start', d.index[0], 'unconditional f20 %.3f f60 %.3f' % (base.f20, base.f60))
print(r.round(3).to_string())
ev = d[(d.pct_chg <= -3) & (d.amt_ratio >= 1.3)]
print(ev[ev.index >= '20230101'][['close', 'pct_chg', 'amt_ratio', 'dd250', 'f20', 'f60']].round(3).to_string())
print('today', d.iloc[-1][['close', 'pct_chg', 'amt_ratio', 'dd250']].round(3).to_dict())
r.to_csv(f'{L}/meta/runs/research/20261119_volume_selloff.csv', index=False)
