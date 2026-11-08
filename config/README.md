# config/

Loaded by `core.Config.load()`: `base.yaml` (committed defaults) deep-merged with `local.yaml`
(git-ignored, machine overrides), then environment (`.env` + shell). Secrets never live here.

## Precedence
1. Environment: `QUANT_CN_LAKE_ROOT` (lake root), `TUSHARE_TOKEN` (only source of the token).
2. `config/local.yaml` (any key below; e.g. `lake.root`, `lake.backup_target`, `download.default_start`).
3. `config/base.yaml`.

## base.yaml keys

| Key | Meaning |
|---|---|
| `lake.root` | Lake root. `~` expanded; relative paths are relative to the repo. Refused inside the repo (D-021). |
| `lake.allow_inside_repo` | `true` only to deliberately allow a root inside the repo (never in commits). |
| `lake.backup_target` | rsync destination for `raw/` + `meta/fetch_log.parquet` (`make lake-backup`). |
| `tushare.url` | Tushare Pro HTTP endpoint. |
| `tushare.timeout_s` | Per-request timeout, seconds. |
| `tushare.page_size` | `limit` per page; paging stops at the first short page. |
| `tushare.retries` | Retries for non-rate-limit failures. |
| `tushare.retry_sleep_s` | Sleep between those retries. |
| `tushare.rate_limit_sleep_s` | Sleep after a rate-limit reply (does not spend retries). |
| `tushare.max_rate_limit_waits` | Rate-limit waits allowed per call before failing. |
| `tushare.rate_limit_markers` | Substrings of the vendor message meaning "rate limited". |
| `tushare.permission_markers` | Substrings meaning "no permission"; the dataset is reported blocked. |
| `download.default_start` | First date for datasets without their own start (D-015b). |
| `download.long_history_start` | First date for `long_history_datasets`. |
| `download.long_history_datasets` | Datasets fetched from `long_history_start`. |
| `download.end` | Last date; `null` = today. |
| `download.order` | Datasets in dependency order (`trade_cal` first). |
| `enum_values.<name>` | Key lists for enum sweeps referenced by `sweep.values_from` (e.g. `indices`). |

## datasets.yaml keys (one entry per dataset; the key is the Tushare endpoint name)

| Key | Meaning |
|---|---|
| `endpoint` | Tushare `api_name`. |
| `sweep.kind` | `none` (one call) · `list_status` / `ts_code` (enum) · `trade_date` (trading days) · `ann_date` (weekdays) · `period` (quarter ends). |
| `sweep.values` / `sweep.values_from` | Enum keys inline, or the name of an `enum_values` list. |
| `sweep.range_params` | Also pass `start_date`/`end_date` to the endpoint. |
| `sweep.extra_params` | Constant parameters (e.g. `exchange: SSE`). |
| `sweep.refetch_recent` | Always refetch the newest N keys (late filers, restatements). |
| `start` | Dataset-specific first date (overrides the download defaults). |
| `refresh` | `append` (fetch each key once) or `overwrite` (refetch every key every run). |
| `primary_key` | Unique key after compaction; duplicates beyond it are dropped and counted in the manifest. |
| `known_on` | The date the row became public (PIT alignment, CODING_STANDARD §2.7); `null` for calendars. |
| `fields` | Columns requested from Tushare and kept in curated/. |
| `text_fields` | Fields stored as text (dates, codes, flags); all other fields are float64. |
| `curated.path` | Location under `curated/`. |
| `curated.partition_by` | Date column for `year=YYYY` partitions; omit for single-file reference tables. |

Adding a dataset with a known `sweep.kind` needs only a new entry here (and it in `download.order`).
