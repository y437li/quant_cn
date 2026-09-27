# quant_cn/

A-share quant research project on a local parquet + DuckDB lake fed by Tushare Pro. Agents start at
`CLAUDE.md`; the coding standard is binding. Structure: `Plans/FOLDER_STRUCTURE.md`.

## Folders
| Folder | Purpose |
|---|---|
| [`.claude/`](.claude/INDEX.md) | agent tooling: class registry, skills, settings |
| [`Plans/`](Plans/INDEX.md) | standards, plans, decisions, data handbook |
| [`config/`](config/INDEX.md) | YAML configuration loaded by `core.Config`, no code |
| [`research_space/`](research_space/INDEX.md) | notebooks that import `quant_cn`; never imported by it |
| [`scripts/`](scripts/INDEX.md) | dev tooling: contract linter, lint runner |
| [`src/`](src/INDEX.md) | `src` layout root holding the `quant_cn` package |
| [`tests/`](tests/INDEX.md) | pytest suite mirroring `src/quant_cn` |

## Files
| File | Purpose | Contains |
|---|---|---|
| `.env.example` | template for the git-ignored `.env`: Tushare token, lake root override | `TUSHARE_TOKEN`, `QUANT_CN_LAKE_ROOT` |
| `.gitignore` | keep lake data, secrets, caches and notebook outputs out of git | |
| `CLAUDE.md` | agent entry point: reading order and non-negotiable rules | |
| `README.md` | project overview: layout, layers, lake zones, setup, data rules | |

_Planned (plan 01 phase 1): `pyproject.toml`, `Makefile`, `.pre-commit-config.yaml`. `data/lake/` is git-ignored and created by `LakeCatalog`._
