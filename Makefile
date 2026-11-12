# All targets run through uv (D-018). The venv lives off the exFAT volume (see DECISIONS).
export UV_PROJECT_ENVIRONMENT ?= $(HOME)/.venvs/quant_cn
UV_RUN := uv run --env-file .env
CLI := $(UV_RUN) python -m quant_cn.cli
# D-067: RUNNER=prefect reports to the local UI; precedence shell env > .env > this default
PREFECT_API_DEFAULT := http://127.0.0.1:4200/api
PREFECT_ENV = $(if $(filter prefect,$(RUNNER)),PREFECT_API_URL="$${PREFECT_API_URL:-$$(sed -n 's/^PREFECT_API_URL=//p' .env 2>/dev/null)}" && export PREFECT_API_URL="$${PREFECT_API_URL:-$(PREFECT_API_DEFAULT)}" &&)

.PHONY: evaluate risk-model release-lags verify-prices setup hooks lint lint-contracts test check doctor download download-dry compact curate lake-rebuild lake-backup notebook project-catalog query prefect-server

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

risk-model:       ## fit the Barra-style risk model (config/risk_model.yaml): derived/risk_* + validation report (plan 05)
	$(CLI) risk-model --no-progress

# --- plan 15: industry-chain web app (APP_STANDARD.md) ------------------------------------------------
GO ?= /opt/homebrew/bin/go
NODE_BIN ?= /opt/homebrew/opt/node@22/bin
WEB_BUILD := $(HOME)/.builds/chain_web
APP_BIN := $(HOME)/.builds/chainapi
APP_DATA ?= research_space/prototypes/chain_view
.PHONY: app app-api app-web app-run app-check app-smoke watchlist etf-proxy manual-series app-charts factor-monitor holdings-risk track-daily track-install track-uninstall

WATCHLIST_DATASETS := daily,daily_basic,report_rc
watchlist:        ## refresh the last 14 days of prices and forecasts, then write $(APP_DATA)/watchlist.json (D-120)
	$(CLI) download --datasets $(WATCHLIST_DATASETS) --start $$(date -v-14d +%Y%m%d)
	$(CLI) compact --datasets $(WATCHLIST_DATASETS)
	$(CLI) watchlist --out $(APP_DATA)

ETF_PROXY_DATASETS := fund_basic,fund_daily,fund_share
manual-series:    ## load config/manual_series.yaml (+ git-ignored local.manual_series.yaml) into curated alt/manual_series (plan 20, D-139)
	$(CLI) download --datasets manual_series
	$(CLI) compact --datasets manual_series

etf-proxy:        ## refresh the last 14 days of ETF prices and shares, then write $(APP_DATA)/etf_proxy.json (D-126)
	$(CLI) download --datasets $(ETF_PROXY_DATASETS) --start $$(date -v-14d +%Y%m%d)
	$(CLI) compact --datasets $(ETF_PROXY_DATASETS)
	$(CLI) etf-proxy --out $(APP_DATA)

app-charts:       ## capture today's App Store game charts (grossing + free, 26 stores) into the lake (D-137, plan 19)
	$(CLI) download --datasets app_store_charts
	$(CLI) compact --datasets app_store_charts

factor-monitor:   ## write $(APP_DATA)/factor_monitor.json from the stored risk-model frames (D-132)
	$(CLI) factor-monitor --out $(APP_DATA)

holdings-risk:    ## value config/local.positions.yaml, decompose its risk, write $(APP_DATA)/holdings_risk.json + lake history (D-132)
	$(CLI) holdings-risk --out $(APP_DATA)

track-daily: watchlist etf-proxy app-charts manual-series  ## what the weekday 18:30 launchd job runs; then curate, refit the risk model, factor monitor, holdings
	$(PREFECT_ENV) $(CLI) curate $(if $(RUNNER),--runner $(RUNNER))
	$(CLI) risk-model --no-progress
	$(CLI) factor-monitor --out $(APP_DATA)
	$(CLI) holdings-risk --out $(APP_DATA)

TRACK_PLIST := $(HOME)/Library/LaunchAgents/com.quantcn.daily-track.plist
TRACK_LOG := $(HOME)/Library/Logs/quant_cn-daily-track.log
track-install:    ## install the weekday 18:30 launchd job that runs make track-daily (log in ~/Library/Logs)
	sed -e "s|@REPO@|$(CURDIR)|g" -e "s|@PATH@|$(dir $(shell command -v uv)):/opt/homebrew/bin:/usr/bin:/bin|g" -e "s|@LOG@|$(TRACK_LOG)|g" scripts/launchd/daily_track.plist.template > $(TRACK_PLIST)
	-launchctl bootout gui/$$(id -u) $(TRACK_PLIST) 2>/dev/null
	launchctl bootstrap gui/$$(id -u) $(TRACK_PLIST)
	@echo "installed $(TRACK_PLIST); log $(TRACK_LOG)"

track-uninstall:  ## unload the launchd job and delete its plist
	-launchctl bootout gui/$$(id -u) $(TRACK_PLIST) 2>/dev/null
	/bin/rm -f "$(TRACK_PLIST)"

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
