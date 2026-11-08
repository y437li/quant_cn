# plans/

Everything that governs the project before and while code exists, organised by document type.
Reading order for a newcomer: `standards/` → `architecture/` → `execution/ROADMAP.md` → the current plan.

| Type | Folder | Answers | Lifecycle |
|---|---|---|---|
| Standards | `standards/` | how code must be written | binding once accepted; changes need a decision |
| Architecture | `architecture/` | what we build and why it is shaped this way | draft → approved → versioned (v1.0, v1.1 …) |
| Execution plans | `execution/` | in what order, by whom, with what done-criteria | see `execution/ROADMAP.md` status vocabulary |
| Decisions | `decisions/` | which choice was made, alternatives, consequences | append-only; superseded, never edited |
| Reference | `reference/` | facts we rely on (vendor API, data catalog) | updated when the facts change |

## Folders
| Folder | Purpose |
|---|---|
| [`architecture/`](architecture/INDEX.md) | design documents: folder and lake layout, src packages, data loading |
| [`decisions/`](decisions/INDEX.md) | the append-only decision log |
| [`execution/`](execution/INDEX.md) | numbered execution plans and the roadmap |
| [`reference/`](reference/INDEX.md) | external facts: Tushare handbook and data catalog |
| [`standards/`](standards/INDEX.md) | binding coding standard |
