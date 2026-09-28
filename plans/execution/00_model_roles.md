# 00 — Model roles: Fable plans and reviews, Opus executes

| | |
|---|---|
| Status | approved 2026-09-27, not applied (config-only change; awaiting "apply 00") |
| Owner | user (approve) / Fable main session (apply: config only, no code) |
| Created | 2026-09-27 |
| Notion | pending |
| Decisions | D-016 |
| Depends on plans | — (prerequisite for executing 01) |

## Goal
Every code-writing action runs on Opus inside a project subagent; planning, decisions and review run on
Fable in the main session; accidental cross-over is blocked by configuration, not memory.

## What Claude Code can and cannot enforce (verified against docs, 2026-09-27)

| Mechanism | Documented | Use |
|---|---|---|
| Subagent `model` in `.claude/agents/<name>.md` (`opus`, `sonnet`, `haiku`, `inherit`, or full ID) | yes | pin the executor to Opus |
| Skill frontmatter `context: fork` + `agent: <name>` | yes | force execution skills to run inside the executor agent |
| Skill frontmatter `model` | no | not available; the agent carries the model |
| `.claude/settings.json` `model` | yes | default the main session to Fable |
| `.claude/settings.json` `availableModels` | yes | restrict `/model` choices to Fable and Opus |
| PreToolUse hook can deny a tool call (JSON `permissionDecision: deny` or exit 2) | yes | block code edits outside an execution run |
| Active model visible to hooks | no | a hook cannot check "am I Fable"; enforce by *path + run marker* instead |
| Prevent `/model` switching at runtime | no | accept; `availableModels` limits the damage |

Consequence: the split is enforced by **where** work runs (executor agent = Opus) and **what** may be
edited (hook on paths), not by inspecting the model. It is **not limited to skills**: skills routed with
`agent: executor` are one entry point, but the hook denies every Edit/Write to code paths from anywhere
except an executor run, so a direct "implement X" in the main session is refused and must be delegated. A user or agent that deliberately creates the run
marker from the main session can bypass it; accidents cannot.

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Executor agent | `.claude/agents/executor.md`: `model: opus`; tools Read, Edit, Write, Bash, Grep, Glob; system prompt = follow CODING_STANDARD §7, edit only `src/ tests/ scripts/ config/ research_space/`, `INDEX.md`, `CLASS_REGISTRY.md`, and the plan's Log table; create `.claude/run/executor.lock` at start, remove at end; report real `make check` output | agent appears in the agent list; a dry task (create a scratch file under `src/`) succeeds via the agent and is refused from the main session | — | todo |
| 2 | Session defaults | `.claude/settings.json`: `"model": "claude-fable-5-1"`, `"availableModels": ["claude-fable-5-1", "claude-opus-5-5"]` | new session in this project starts on Fable; `/model` offers only the two | — | todo |
| 3 | Edit guard hook | `.claude/hooks/guard_code_paths.sh` + `PreToolUse` entry (matcher `Edit|Write|MultiEdit|NotebookEdit`): deny when target path is under `src/ tests/ scripts/ config/ research_space/` and `.claude/run/executor.lock` is absent; always allow `plans/`, `.claude/`, `INDEX.md`, `CLAUDE.md` | main-session Edit to `src/x.py` is denied with a reason naming this plan; the same edit inside the executor succeeds | 1 | todo |
| 4 | Skill routing | `new-class` and `test-cases` gain `context: fork`, `agent: executor`; `plan` skill: execute mode says "delegate the phase to the executor agent; run `standard-review` only when the user asks"; `standard-review`, `decisions`, `plan` (create/update), `registry` lookup stay in the main session | invoking `new-class` shows it running in the executor; `standard-review` runs in main | 1 | todo |
| 5 | Documentation | CLAUDE.md role rule; CODING_STANDARD §7 step list names the model for each step; D-016 accepted; INDEX.md for `.claude/agents/`, `.claude/hooks/`, `.claude/run/` | `index` skill check clean; D-016 accepted | 1–4 | todo |

## Files to create (exact content in phase 1–3)

`.claude/agents/executor.md`
```markdown
---
name: executor
description: Opus execution agent. Implements an approved plan phase the quant_cn way (contract-first classes, tests, make check). Use for any change to src/, tests/, scripts/, config/, research_space/. Never plans or reviews.
model: opus
tools: Read, Edit, Write, Bash, Grep, Glob
---
You execute one approved plan phase from plans/execution/NN_*.md. Before anything: read CLAUDE.md,
plans/standards/CODING_STANDARD.md, .claude/CLASS_REGISTRY.md, the plan. Then `mkdir -p .claude/run && touch .claude/run/executor.lock`.
Follow CODING_STANDARD §7 for every class (new-class skill). You may edit only: src/, tests/, scripts/,
config/, research_space/, any INDEX.md, .claude/CLASS_REGISTRY.md, and the Log table of the plan you execute.
You never edit plans/*.md bodies, DECISIONS.md, CLAUDE.md or skills; if a plan is wrong, stop and report.
Finish with `make check` (paste real output), update registry and indexes, `rm .claude/run/executor.lock`,
and report: files touched, classes created/extended/reused, test output, anything left out.
```

`.claude/settings.json`
```json
{
  "model": "claude-fable-5-1",
  "availableModels": ["claude-fable-5-1", "claude-opus-5-5"],
  "hooks": {
    "PreToolUse": [
      { "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [ { "type": "command", "command": ".claude/hooks/guard_code_paths.sh" } ] }
    ]
  }
}
```

`.claude/hooks/guard_code_paths.sh` (reads tool_input.file_path from stdin JSON; exit 2 with reason when
the path is a code path and `.claude/run/executor.lock` is missing).

## Risks
- Hook cannot see the model: enforcement is by path and run marker; a deliberate bypass is possible and visible (`executor.lock` created from main).
- The executor forgets to remove the lock: stale lock lets main edit code. Mitigation: hook also denies when the lock is older than 6 hours; `make check` fails if the lock exists at the end.
- `availableModels` is documented as admin/managed-level in some contexts; if ignored at project level, phase 2 degrades to the `model` default only. Verify in phase 2.
- Alias `fable` is not in the documented subagent alias list; the main session uses the full ID `claude-fable-5-1` in settings, and the executor uses the documented alias `opus`.

## Open questions
None. Closed 2026-09-27:
- Fable review is **not** automatic per phase; it runs only when the user asks (`standard-review` / `code-review`).
- `test-cases` scaffolding runs on Opus (executor); audit mode is a review task and runs on Fable when asked.

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-09-27 | — | Plan approved by user ("approve"); application waits for an explicit instruction |
| 2026-09-27 | 4 | User: review only on request, not per phase; skill routing text updated |
| 2026-09-27 | — | Drafted after verifying mechanisms against Claude Code docs (sub-agents, skills, hooks, settings-reference) |
