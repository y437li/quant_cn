---
name: decisions
description: Record, look up or revisit project decisions in Plans/DECISIONS.md (lightweight ADR log). Use whenever a design, data, tooling or scope choice is made or changed, when the user says "decide", "we'll go with", "log this decision", "why did we choose", or when a plan or code change contradicts an earlier decision.
---

# decisions

One append-only log: `Plans/DECISIONS.md`. Every entry is short enough to read in 20 seconds.

## When to record
- A choice between alternatives that later code will depend on (library, schema, layout, rule).
- A change to an earlier decision (new entry that **supersedes** the old one; never edit history).
- A user instruction that overrides a default or the coding standard.
Do not record routine implementation details that the code itself explains.

## Entry format (append to the table and the detail list)

Table row:
`| D-NNN | YYYY-MM-DD | <title, <= 8 words> | accepted | <plan or file> |`

Detail block:
```
### D-NNN <title>
- Context: one line, the problem or fork.
- Decision: one line, what we do.
- Alternatives: a / b (rejected because …)   <- one line each, max 3
- Consequences: what becomes easier / harder, what must follow (e.g. class to build, rule in standard).
- Links: plan NN, CODING_STANDARD §x, DATA_CATALOG §y
```
Status values: `proposed` | `accepted` | `superseded by D-MMM` | `rejected`.

## Procedure
1. Read `Plans/DECISIONS.md`; check whether the topic already has an entry. If yes and it still holds, cite it instead of writing a new one.
2. If the user has not chosen yet, write the entry as `proposed` with alternatives and stop for their call.
3. On acceptance, set `accepted`, and update anything the decision governs in the same change: `CODING_STANDARD.md`, the affected plan's `Decisions` header, `.claude/CLASS_REGISTRY.md` if a class is renamed or retired.
4. When a decision is reversed, add the new entry and mark the old row `superseded by D-NNN`.

## Lookup
"Why did we …": grep the title and context columns, quote the entry ID and the Decision line. Do not paraphrase from memory.

## Report
Return the entry ID(s) touched and one line each. Nothing else.
