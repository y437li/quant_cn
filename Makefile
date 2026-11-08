# All targets run through uv (D-018). The venv lives off the exFAT volume (see DECISIONS).
export UV_PROJECT_ENVIRONMENT ?= $(HOME)/.venvs/quant_cn
UV_RUN := uv run --env-file .env
CLI := $(UV_RUN) python -m quant_cn.cli
# D-067: RUNNER=prefect reports to the local UI; precedence shell env > .env > this default
PREFECT_API_DEFAULT := http://127.0.0.1:4200/api
PREFECT_ENV = $(if $(filter prefect,$(RUNNER)),PREFECT_API_URL="$${PREFECT_API_URL:-$$(sed -n 's/^PREFECT_API_URL=//p' .env 2>/dev/null)}" && export PREFECT_API_URL="$${PREFECT_API_URL:-$(PREFECT_API_DEFAULT)}" &&)

.PHONY: evaluate release-lags verify-prices setup hooks lint lint-contracts test check doctor download download-dry compact curate lake-rebuild lake-backup notebook project-catalog query prefect-server

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

check: lint test app-check project-catalog release-lags  ## everything a change must pass; refreshes schema project

doctor:           ## lake root, free space, token presence
	$(CLI) doctor

download:         ## e.g. make download ARGS="--datasets daily --start 20260801" [RUNNER=prefect]
	$(PREFECT_ENV) $(CLI) download $(if $(RUNNER),--runner $(RUNNER)) $(ARGS)

download-dry:     ## list keys to fetch without calling the API
	$(CLI) download --dry-run $(ARGS)

compact:          ## raw -> curated partitions
	$(CLI) compact $(ARGS)

curate:           ## compact raw -> curated, derived views, PIT states, indexes, digests [RUNNER=prefect]
	$(PREFECT_ENV) $(CLI) curate $(if $(RUNNER),--runner $(RUNNER)) $(ARGS)

lake-rebuild:     ## recreate catalog + fetch log from parquet, then curate (digests "unchanged" = identical)
	$(CLI) rebuild
	$(CLI) curate --no-progress

lake-backup:      ## rsync raw/ + fetch log to lake.backup_target (config/local.yaml)
	$(CLI) backup

notebook:         ## run research_space/main.ipynb top to bottom against the lake (outputs discarded)
	$(UV_RUN) jupyter nbconvert --to notebook --execute research_space/main.ipynb --stdout > /dev/null
	@echo "main.ipynb ran top to bottom"

project-catalog:  ## rebuild schema `project` (repo tree, registry, plans, decisions, lint) in the lake catalog
	$(CLI) project-catalog $(ARGS)

query:            ## read-only SQL against the lake catalog, e.g. make query SQL="SELECT * FROM project.todo"
	$(CLI) query "$(SQL)"

prefect-server:   ## start the local Prefect UI (http://127.0.0.1:4200); then use RUNNER=prefect
	$(UV_RUN) prefect server start

release-lags:     ## warn when a macro release-lag rule is earlier than an observed release (D-086)
	$(CLI) release-lags

VERIFY_START ?= $(shell python3 -c "import datetime as d; print((d.date.today() - d.timedelta(days=10)).strftime('%Y%m%d'))")
verify-prices:    ## BaoStock cross-check of the last ~5 sessions (D-085): refetch, curate, report mismatch rate
	$(CLI) download --datasets baostock_daily_recent --start $(VERIFY_START) --force --no-progress
	$(CLI) curate --datasets baostock_daily_recent --no-progress
	$(CLI) query "SELECT * FROM quality.price_crosscheck WHERE trade_date >= '$(VERIFY_START)' ORDER BY trade_date"

evaluate:         ## evaluate the factor campaign (config/factors.yaml): reports + trial log (plan 04 phase 5)
	$(CLI) evaluate --no-progress

# --- plan 15: industry-chain web app (APP_STANDARD.md) ------------------------------------------------
GO ?= /opt/homebrew/bin/go
NODE_BIN ?= /opt/homebrew/opt/node@22/bin
WEB_BUILD := $(HOME)/.builds/chain_web
APP_BIN := $(HOME)/.builds/chainapi
APP_DATA ?= research_space/prototypes/chain_view
.PHONY: app app-api app-web app-run app-check app-smoke

app-api:          ## build the Go API binary into ~/.builds (off the exFAT volume)
	cd apps/chain_api && $(GO) vet ./... && $(GO) build -buildvcs=false -o $(APP_BIN) ./cmd/chainapi

app-web:          ## mirror apps/chain_web to ~/.builds, install, typecheck, build, copy dist to apps/chain_api/web/dist
	mkdir -p $(WEB_BUILD) && rsync -a --delete --exclude node_modules --exclude dist apps/chain_web/ $(WEB_BUILD)/
	cd $(WEB_BUILD) && PATH=$(NODE_BIN):$$PATH npm install --no-audit --no-fund --cache $(HOME)/.builds/npm-cache && PATH=$(NODE_BIN):$$PATH npx tsc --noEmit && PATH=$(NODE_BIN):$$PATH npx vite build
	rm -rf apps/chain_api/web/dist && cp -R $(WEB_BUILD)/dist apps/chain_api/web/dist

app: app-api app-web  ## build the whole app

app-run: app      ## build and serve the app on http://127.0.0.1:8787 (local only)
	$(APP_BIN) -data $(APP_DATA) -web apps/chain_api/web/dist

app-check:        ## go vet + go test + tsc + vitest
	cd apps/chain_api && $(GO) vet ./... && $(GO) test ./...
	mkdir -p $(WEB_BUILD) && rsync -a --delete --exclude node_modules --exclude dist apps/chain_web/ $(WEB_BUILD)/
	cd $(WEB_BUILD) && PATH=$(NODE_BIN):$$PATH npx tsc --noEmit && PATH=$(NODE_BIN):$$PATH npx vitest run

app-smoke:        ## Playwright smoke run against a running app (make app-run in another shell)
	rsync -a --delete --exclude node_modules --exclude dist apps/chain_web/ $(WEB_BUILD)/ && cd $(WEB_BUILD) && PATH=$(NODE_BIN):$$PATH node tests/smoke.mjs
