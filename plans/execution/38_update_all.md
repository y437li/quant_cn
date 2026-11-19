# 38 — Update task ledger and `update-all` (任务表与一键更新)

| | |
|---|---|
| Status | done 2026-11-18 (ph1–3) |
| Owner | user (approve) / executor (build) |
| Created | 2026-11-18 |
| Notion | pending |
| Decisions | D-181, D-022, D-101 |
| Depends on plans | 15 ph7 (app, APP_DATA), 22 (notify), 02 (lake catalog) |

## Goal
One command, `make update-all`, runs every daily update in order, keeps going past a failed step, and writes one row per step to a parquet task ledger (`meta/task_log/`). The app and the morning e-mail then show which steps ran, failed or were skipped, and the date each output reaches.

## Today
- `make track-daily` already runs 16 targets and then curate, risk-model, factor-monitor and holdings-risk in sequence, but make stops at the first failure, and nothing records per-step status. The only record is `~/Library/Logs/quant_cn-daily-track.log`.
- `meta/fetch_log.parquet` records raw downloads per (dataset, key), not tasks. `meta.run_log` (RunLog, D-022) is in DuckDB, so writing it during the run would hold the single-writer catalog lock that the steps themselves need.

## Scope
- In:
  - `config/update_all.yaml`: ordered steps. Each step has a name, a make target, `needs` (steps that must succeed first), an optional output JSON (read for its `as_of`) and whether it writes the lake.
  - Task ledger: one zstd parquet part per step under `meta/task_log/` (tmp + rename, no catalog lock, like DocumentManifestWriter, D-101); a view `meta.task_log` refreshed once at the end. Columns: run_id, trigger (launchd / manual), task, target, started_at, finished_at, duration_s, status (ok / failed / skipped), exit_code, as_of, output, message (last 20 output lines on failure).
  - `update-all` CLI and make target:
    - Runs the steps in order; skips a step whose `needs` failed.
    - Prints a summary table and exits non-zero if any step failed.
    - Flags: `--only`, `--from`, `--dry-run` (print the plan), `--with-report` (morning-report at the end).
    - `track-daily` becomes `update-all`, so the launchd job is unchanged.
  - `APP_DATA/task_status.json`: the latest run, plus the last success and the last 10 runs of each step. Shown on an app panel (监测 → 更新状态) and as one line in the 持仓监测 e-mail ("更新 17/18 成功；失败：…").
- Out:
  - Parallel steps.
  - Automatic retries, beyond one optional retry for a step marked `retry: 1`.
  - The iMessage `notify` step: `update-all` never sends to 妈妈; holdings-risk runs through the CLI.
  - Changing what each make target does.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Ledger | `core.UpdateAllSettings` (config/update_all.yaml, validated: unknown make target, unknown or later `needs`); `lake.TaskLog` (append part, read the ledger, refresh view) | Tests: settings validation, parts written atomically, view returns rows, crash between steps keeps earlier rows; `make check` green | — | done 2026-11-18 — `core.UpdateAllSettings` / `UpdateStep`, `lake.TaskLog` (view hooked into LakeCatalog.refresh_views); TC-UAS-001..003, TC-TKL-001..003 |
| 2 | Runner | `pipeline.UpdateAllRunner` (injected process runner + clock: run, skip on failed needs, capture tail, read output `as_of`); `cli` command `update-all`; make `update-all`, `track-daily` delegates | Tests with a fake process runner (fail → dependents skipped, others run; exit code; dry-run); one real `make update-all` with its summary and ledger rows pasted; `make check` green | 1 | done 2026-11-18 — `pipeline.UpdateAllRunner`, `MakeTargetRunner`, `cli.UpdateCommands`; make `update-all`, `holdings-risk-data`, `track-daily` delegates; TC-UAR-001..003, TC-MKR-001, TC-UPC-001..002; real run 20261118T225855: 19/19 ok in 43 min (market-data 385 s, curate 678 s, risk-model 780 s), 19 ledger rows, meta.task_log queryable |
| 3 | Display | `task_status.json` writer; Go `GetTaskStatus` + `/api/tasks`; app panel 更新状态; e-mail line via a ReportSection | go test, vitest, smoke opens the panel; dry-run e-mail shows the line; `make check` green | 2 | done 2026-11-18 — `pipeline.TaskStatusBuilder` (TC-TSB-001..002), Go `GetTaskStatus` + `/api/tasks` (TC-ST-032, TC-API-019), app 监测 → 更新状态 (TC-TKF-001..002; smoke "tasks: 19 steps; 最近一次 11-18 22:58（手动）：19/19 成功。"), `visualization.TaskStatusReportSection` (TC-TSR-001..002; dry-run e-mail line "数据更新 11-18 22:58（手动）：19/19 成功。"); make check: lint 0, 1123 passed, go ok, vitest 62 passed; project-catalog step blocked by another session's catalog lock |

Status cell: `<state> <YYYY-MM-DD> (<commit>) — <note>`, state one of todo / doing / blocked / done.

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `UpdateAllSettings` | new | core | 1 |
| `TaskLog` | new (part pattern of `DocumentManifestWriter`; not `RunLog`, see D-181) | lake | 1 |
| `LakeCatalog` | reuse (view refresh) | lake | 1 |
| `Clock` | reuse | core | 1–2 |
| `UpdateAllRunner` | new | pipeline | 2 |
| `ResearchCommands` or `QuantCnCli` | extend (command `update-all`) | cli | 2 |
| `TaskStatusReportSection` | new | visualization | 3 |
| `ReportCommands` | extend (section list) | cli | 3 |
| Go `store` / `api` | extend (`GetTaskStatus`, route `tasks`) | apps/chain_api | 3 |

## Risks
- Another session holds the catalog writer lock, so a download or compact step fails. Mitigation: the step is marked failed with the lock message and the rest go on. `--from <step>` reruns from that point.
- Make targets that change later go out of step with config/update_all.yaml. Mitigation: settings validation checks every target exists in the Makefile (`make -n`).
- A step hangs (network). Mitigation: a per-step `timeout_min` in the config (default 30); a timeout is marked failed.
- Output `as_of` keys differ between JSON files. Mitigation: read `as_of` when present, else leave it null; no per-file parsing.

## Open questions
- Should the app panel sit under 监测 or a new 系统 entry? Default: 监测 → 更新状态.
- Should `--with-report` be the launchd default, so the e-mail goes out after the 06:00 run, or stay manual (memory: the user asks for the morning update by hand)? Default: stay manual.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-18 | — | drafted (user: "写计划38，任务表和 update-all") |
| 2026-11-18 | 2 | peer note: plan 21 ph5 adds a daily step `retail-gauge` (needs market-data; before morning-report; catalog write only for a brief view refresh at the end). Add it to config/update_all.yaml if ph2 has landed when it is wired |
| 2026-11-18 | 1–3 | done; first real run 19/19 ok; open questions kept at defaults (panel under 监测; launchd run sends no e-mail). TaskLog types text columns as string so null as_of reads as VARCHAR in the view |
