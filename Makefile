# All targets run through uv (D-018). The venv lives off the exFAT volume (see DECISIONS).
export UV_PROJECT_ENVIRONMENT ?= $(HOME)/.venvs/quant_cn
UV_RUN := uv run --env-file .env
CLI := $(UV_RUN) python -m quant_cn.cli

.PHONY: setup hooks lint lint-contracts test check doctor download download-dry compact curate lake-rebuild lake-backup

setup:            ## create the venv from uv.lock; copy .env.example to .env if missing
	uv sync --all-extras
	@test -f .env || (cp .env.example .env && echo "created .env: set TUSHARE_TOKEN")

hooks:            ## install the pre-commit hooks (.pre-commit-config.yaml)
	uv run pre-commit install

lint:             ## ruff format check, ruff lint, mypy strict, import layers, contract linter
	uv run ruff format --check src tests scripts
	uv run ruff check src tests scripts
	uv run mypy
	uv run lint-imports
	uv run python scripts/lint_contracts.py

lint-contracts:   ## contract/index/size/names linter only, e.g. make lint-contracts ARGS=--index
	uv run python scripts/lint_contracts.py $(ARGS)

test:             ## offline test suite with coverage
	uv run pytest --cov

check: lint test  ## everything a change must pass

doctor:           ## lake root, free space, token presence
	$(CLI) doctor

download:         ## e.g. make download ARGS="--datasets daily --start 20260801"
	$(CLI) download $(ARGS)

download-dry:     ## list keys to fetch without calling the API
	$(CLI) download --dry-run $(ARGS)

compact:          ## raw -> curated partitions
	$(CLI) compact $(ARGS)

curate:           ## compact raw -> curated, derived views, PIT states, indexes, digests
	$(CLI) curate $(ARGS)

lake-rebuild:     ## recreate catalog + fetch log from parquet, then curate (digests "unchanged" = identical)
	$(CLI) rebuild
	$(CLI) curate --no-progress

lake-backup:      ## rsync raw/ + fetch log to lake.backup_target (config/local.yaml)
	$(CLI) backup
