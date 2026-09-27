# All targets run through uv (D-018). The venv lives off the exFAT volume (see DECISIONS).
export UV_PROJECT_ENVIRONMENT ?= $(HOME)/.venvs/quant_cn
UV_RUN := uv run --env-file .env
CLI := $(UV_RUN) python -m quant_cn.cli

.PHONY: setup lint test check doctor download download-dry compact lake-rebuild lake-backup

setup:            ## create the venv from uv.lock; copy .env.example to .env if missing
	uv sync --all-extras
	@test -f .env || (cp .env.example .env && echo "created .env: set TUSHARE_TOKEN")

lint:             ## ruff format check, ruff lint, mypy strict, import layers
	uv run ruff format --check src tests
	uv run ruff check src tests
	uv run mypy
	uv run lint-imports

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

lake-rebuild:     ## recreate DuckDB catalog + fetch log from parquet, then recompact
	$(CLI) rebuild
	$(CLI) compact

lake-backup:      ## rsync raw/ + fetch log to lake.backup_target (config/local.yaml)
	$(CLI) backup
