---
name: plan
description: Write, update or execute a concise project plan in plans/execution/ and mirror its phases to Notion. Use when the user asks to "plan", "make a plan", "draft a plan", "update the plan", "start phase N", "what's next", or before any non-trivial implementation (required by CLAUDE.md). Plans are short: goal, scope, phases with done-criteria, classes touched, risks.
---

# plan

Source of truth is the markdown file in `plans/execution/`. Notion is a mirror for phase tracking.
Never let the two disagree: every phase status change is written to the file first, then Notion.

## Principles (best practice, keep it short)
- One page. If it needs more, the scope is too big; split into plans.
- Every phase has a **deliverable** and a **done criterion** that can be checked, not felt.
- Name the classes: new / extended / reused (from `.claude/CLASS_REGISTRY.md`). No class, no phase.
- Decisions go in `plans/decisions/DECISIONS.md` via the `decisions` skill; the plan only links their IDs.
- No prose that explains why something is obvious. Bullets, tables, imperative verbs.
- Status vocabulary: `todo` | `doing` | `blocked` | `done`. Nothing else.

## Modes

### 1. Create
1. Read `CLAUDE.md`, `plans/standards/CODING_STANDARD.md`, `.claude/CLASS_REGISTRY.md`, `plans/decisions/DECISIONS.md`, `plans/execution/ROADMAP.md`, the design in `plans/architecture/` the plan implements, and any existing plan that overlaps. Reuse, do not duplicate.
2. Copy `plan_template.md` (beside this file) to `plans/execution/NN_<slug>.md` (`NN` = next two-digit number).
3. Fill it. Hard limits: <= 6 phases, <= 3 bullets per phase, <= 5 risks. Unknowns go under **Open questions**, never guessed. Add the plan's row to `ROADMAP.md` (status `drafted, awaiting approval`) and its file row to `plans/execution/INDEX.md`.
4. Sync to Notion (Section "Notion sync"). Record the Notion page URL in the plan header.
5. Stop and hand the plan to the user for approval. Do not start implementation in the same turn.

### 2. Update
1. Edit the plan file: status, done-criterion evidence (test output, file paths), new open questions.
2. Append one line to the plan's **Log** table: `date | phase | change`. If the plan's status changed, update its row in `plans/execution/ROADMAP.md`.
3. Sync the changed phases to Notion.

### 3. Execute (follow the plan)
1. Open the plan; find the first phase with status `todo` whose dependencies are `done`.
2. Mark it `doing` (file + Notion). Work only inside that phase's scope.
3. Follow `CODING_STANDARD.md` §7 for each class (contract -> `test-cases` skill -> implement -> ruff/pytest -> registry).
4. When the done criterion is met with evidence, mark `done`; otherwise `blocked` with the reason. Never skip to the next phase while one is `blocked` without telling the user.
5. If execution reveals the plan is wrong, stop, update the plan (mode 2), record a decision, then continue.

## Notion sync
1. Load tools: `ToolSearch("+notion")`. If only `mcp__notion__authenticate` exists, call it, give the user the URL, and complete auth with the callback URL. If the user cannot authenticate now, continue local-only and say so in the report; set `notion: pending` in the plan header.
2. First sync of a plan: create one Notion page titled `<NN> <Plan title>` under the workspace's `quant_cn / Plans` parent (ask the user for the parent once; store its ID in `.claude/notion.json`). The page contains a **Phases** database with properties: `Phase` (title), `Status` (select: todo/doing/blocked/done), `Deliverable` (text), `Done criterion` (text), `Depends on` (text), `Updated` (date).
3. Later syncs: update only rows whose status or text changed. Never delete rows; a dropped phase becomes status `done` with deliverable text `dropped: <reason>`.
4. Store the page URL and database ID in the plan header so the next agent can find them without searching.

## Report format (after any mode)
- Plan file path, Notion URL (or `pending`).
- Phase table: phase | status | evidence.
- Open questions needing the user.
Nothing else.
