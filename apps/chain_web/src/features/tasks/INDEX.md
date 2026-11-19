# apps/chain_web/src/features/tasks/

更新状态 page at `#tasks` (plan 38, D-181). Read-only display of `GET /api/tasks` (task_status.json from the Python `TaskStatusBuilder`).

## Files
| File | Purpose | Contains |
|---|---|---|
| `tasks-page.tsx` | headline of the latest run; per step state, time, data date, last success, recent runs as dots, failure note | `TasksPage` |
| `tasks-format.ts` | pure helpers: duration text, headline, state labels | `formatDuration`, `taskHeadline`, `STATE_LABEL` |
| `tasks-format.test.ts` | vitest TC-TKF-001..002 |  |
