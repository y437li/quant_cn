"""融资余额 / 流通市值 since 2019 (margin_detail sum over daily_basic circ_mv), with 中证1000."""
import duckdb
L = '/Volumes/Treasury/quant_cn_lake'
c = duckdb.connect()
df = c.sql(f"""
with m as (select trade_date, sum(rzye)/1e8 rz, count(*) n from read_parquet('{L}/curated/margin_detail/**/*.parquet', union_by_name=true)
           where trade_date >= '20181201' group by 1),
b as (select trade_date, sum(circ_mv)/1e4 circ from read_parquet('{L}/curated/daily_basic/**/*.parquet', union_by_name=true)
      where trade_date >= '20181201' group by 1),
i as (select trade_date, close from read_parquet('{L}/curated/reference/index_daily.parquet') where ts_code='000852.SH')
select m.trade_date, rz, n, circ, rz/circ*100 AS share, i.close AS small from m join b using(trade_date) left join i using(trade_date) order by 1
""").df()
df = df[df.n >= 0.9 * df.n.rolling(20, min_periods=1).median()]
df = df[df.trade_date >= '20190101']
df.to_csv(f'{L}/meta/runs/research/20261119_margin_share.csv', index=False)
print(df.iloc[[0, -1]].round(2).to_string())
print('min', df.loc[df.share.idxmin(), ['trade_date', 'share']].tolist(), 'max', df.loc[df.share.idxmax(), ['trade_date', 'share']].tolist())
df['y'] = df.trade_date.str[:4]
print(df.groupby('y').share.agg(['min', 'max', 'median']).round(2))
for a, b in [('20190101', '20190301'), ('20200301', '20200501'), ('20220401', '20220601'), ('20240101', '20240301'), ('20240801', '20241001'), ('20250401', '20250501')]:
    s = df[(df.trade_date >= a) & (df.trade_date < b)]
    r = s.loc[s.share.idxmin()]
    print('trough', r.trade_date, round(r.share, 2), round(r.small or 0))

# share on 中证1000 bottoms (lowest close in each window) and the share low within +-30 sessions
print('index bottoms')
for a, b in [('20181201', '20190301'), ('20200101', '20200501'), ('20220301', '20220601'), ('20231201', '20240301'), ('20240801', '20241001'), ('20250301', '20250501')]:
    s = df[(df.trade_date >= a) & (df.trade_date < b)]
    r = s.loc[s.small.idxmin()]
    i = df.index.get_loc(r.name)
    w = df.iloc[max(0, i - 30): i + 30]
    lo = w.loc[w.share.idxmin()]
    print(r.trade_date, 'small', round(r.small), 'share', round(r.share, 2), '| window low', lo.trade_date, round(lo.share, 2))
