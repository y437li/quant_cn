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
| `.pre-commit-config.yaml` | commit hooks: ruff format/check, mypy, lint-imports, lint_contracts via uv | |
| `.python-version` | Python version read by uv | `3.12` |
| `CLAUDE.md` | agent entry point: reading order and non-negotiable rules | |
| `Makefile` | uv-run targets: setup, lint, test, check, doctor, download, compact, lake-rebuild, lake-backup | |
| `README.md` | project overview: layout, layers, lake zones, setup, data rules | |
| `pyproject.toml` | package metadata, dependencies, ruff/mypy/pytest/coverage/import-linter config | |
| `uv.lock` | exact resolved dependency versions (D-018) | |

_The lake lives outside the repo (D-021); `.env` is git-ignored._
