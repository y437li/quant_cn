---
name: research-log
description: Record an ad-hoc analysis (screen, event study, stock review, curve, what-if) so it survives the session - scripts into research_space/runs/<YYYYMMDD>_<topic>/, outputs into the lake meta/runs/research/, one row in research_space/RESEARCH_LOG.md. Use before ending any answer that ran analysis code outside src/, when the user asks "where did we look at X", "redo that analysis", "what have we researched", or when promoting an analysis into a plan.
---

# research-log

The log is `research_space/RESEARCH_LOG.md` (D-144, plan 02 ph6). The catalog loads it into `project.research_runs`; `make lint` (group `research`) checks it.

## Record a run
1. Slug: `YYYYMMDD_<topic>` (topic snake_case, ≤ 4 words; `naming` skill). Date = the day of the analysis.
2. Scripts: copy them from the session scratchpad into `research_space/runs/<slug>/` (or point at an existing prototype folder). In each script:
   - lake paths from `Config.load().lake.root`, never a hard-coded volume path;
   - outputs to `<lake>/meta/runs/research/<slug>/`, never into git;
   - private data only at runtime: `PositionsBook.load(repo_root)`, `config/local.*`; no held codes, costs or cash in the file (lint fails at 5 held codes or one cost / cash figure).
3. Run every script once from the repo root (`uv run [--env-file .env] python research_space/runs/<slug>/<file>.py`) and check it reproduces the numbers given to the user. If one cannot run now (lake lock, API), say so in the row's Conclusion.
4. Write `research_space/runs/<slug>/INDEX.md` (question, run order, one row per file) and add the folder to `research_space/runs/INDEX.md`.
5. Add the row at the top of the log table: Date | Slug | Question (the user's words) | Scripts | Outputs | Conclusion (one line, numbers included, no private amounts) | Follow-up (plan / decision IDs, watchlist entry, or `none`).
6. `uv run python scripts/lint_contracts.py --research --index` must report 0.

## Look up
- `make query SQL="SELECT date, slug, question, conclusion FROM project.research_runs ORDER BY date DESC"`
- A follow-up that became a plan phase or decision is the link between exploration and code; keep it current when the plan changes.
