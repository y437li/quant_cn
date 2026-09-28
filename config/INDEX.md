# config/

Configuration only, no code. Loaded by `core.Config`; secrets never live here (env only).

## Files
| File | Purpose | Contains |
|---|---|---|
| `README.md` | meaning and precedence of every configuration key |  |
| `base.yaml` | lake root default, Tushare paging/retry settings, download order and start dates, enum key lists | `lake`, `tushare`, `download`, `enum_values` |
| `datasets.yaml` | one entry per dataset: endpoint, sweep, primary key, known-on column, fields, curated layout | 17 datasets |
