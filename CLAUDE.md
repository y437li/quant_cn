# quant_cn — agent instructions

Read these before any work, in this order:
0. `INDEX.md` — root of the folder index tree; follow it down to find any file.
1. `Plans/CODING_STANDARD.md` — binding coding standard (OOP, contracts, tests, layering).
2. `.claude/CLASS_REGISTRY.md` — what already exists. Search it before writing any class or function.
3. `Plans/fresh_start/` — domain handbook: Tushare API rules, data catalog, point-in-time traps. Data semantics there win over guesses.
4. `Plans/DECISIONS.md` — decisions already taken; do not re-open them silently.
5. The current plan in `Plans/plans/` for the task at hand.

Non-negotiable rules:
- Plan first. Use the `plan` skill to write or update a plan in `Plans/plans/` and get approval before writing code for any non-trivial task.
- Log every design/data/tooling choice with the `decisions` skill. A change that contradicts an accepted decision needs a superseding entry first.
- Object-oriented only. No loose functions outside `core/utils` (and those need registry justification).
- Every class and public method has the docstring contract: Purpose / Contract (Input, Output, Raises) / Test cases.
- Never duplicate. If the registry or `grep` shows a near-match, extend or subclass it.
- Build every class with the `new-class` skill (search -> contract -> tests -> code -> verify). Look up and update `.claude/CLASS_REGISTRY.md` with the `registry` skill.
- Use the `test-cases` skill to derive tests from the contract before implementing.
- Run the `standard-review` skill before calling any code task or plan phase done.
- A change is done only when `make check` passes (paste real output), the registry row and block are updated, and every touched folder's `INDEX.md` is current.
