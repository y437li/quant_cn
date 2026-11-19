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
.PHONY: update-all holdings-risk-data retail-gauge opportunity-list app app-api app-web app-run app-check app-smoke watchlist etf-proxy etf-cta manual-series app-charts factor-monitor holdings-risk macro-monitor futures-monitor volatility-monitor smallcap-watch rates-fx-monitor sector-monitor sector-earnings-signal notify market-data margin-panel buyback-events track-daily track-install track-uninstall morning-report report-install report-uninstall

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

# every daily market dataset, refreshed by track-daily (user: "我们的数据应该每天都更新")
MARKET_DATASETS := daily,daily_basic,adj_factor,moneyflow,stk_limit,margin,margin_detail,hk_hold,fund_daily,fund_share,fut_daily,fut_holding,opt_daily,stk_holdertrade,repurchase,cyq_perf,sw_daily,report_rc,stk_surv
# overwrite / date-window datasets refresh their own recent range: no --start (D-049)
MARKET_RANGE_DATASETS := index_daily,fut_basic,shibor,fx_daily,cn_bond_yield,cny_fixing,us_treasury_yield,cboe_vix
market-data:      ## refresh the last 14 days of every daily market dataset (stocks, flows, margin, northbound, ETFs, futures, options, rates, FX)
	$(CLI) download --datasets $(MARKET_DATASETS) --start $$(date -v-14d +%Y%m%d) --no-progress
	$(CLI) download --datasets $(MARKET_RANGE_DATASETS) --no-progress
	$(CLI) compact --datasets $(MARKET_DATASETS),$(MARKET_RANGE_DATASETS)

notify:           ## send the new plain-language alerts by iMessage with card pictures (config/local.notify.yaml; plan 22, D-153). NOTIFY_ARGS=--dry-run to preview
	rsync -a --delete --exclude node_modules --exclude dist apps/chain_web/ $(WEB_BUILD)/
	$(CLI) notify --data $(APP_DATA) --node $(NODE_BIN)/node --shot-script $(WEB_BUILD)/tests/shot_cards.mjs --images $(HOME)/Pictures/quant_cn_alerts $(NOTIFY_ARGS)

volatility-monitor:  ## write $(APP_DATA)/volatility_monitor.json: US VIX (CBOE) + A-share VIX from options (config/volatility_monitor.yaml; plan 03 ph6, D-152)
	$(CLI) volatility-monitor --out $(APP_DATA)

rates-fx-monitor: ## write $(APP_DATA)/rates_fx_monitor.json: 利率与汇率 (中债 curve, spreads, 股债性价比, RMB vs majors, fixing; config/rates_fx_monitor.yaml; plan 34)
	$(CLI) rates-fx-monitor --out $(APP_DATA)

smallcap-watch:   ## write $(APP_DATA)/smallcap_watch.json: 小盘观察 (limit-downs, 60-day lows, 中证1000 levels, vol gap, broad-ETF flows; config/smallcap_watch.yaml; plan 30)
	$(CLI) smallcap-watch --out $(APP_DATA)
retail-gauge:     ## 散户温度计 daily reading for today -> derived/retail_gauge (plan 21, D-142 / D-155 / D-167)
	$(CLI) retail-gauge

opportunity-list: ## daily opportunity list -> derived/opportunity_list + $(APP_DATA)/opportunities.json (plan 21 ph4-5)
	$(CLI) opportunity-list --out $(APP_DATA)

sector-earnings-signal: ## write $(APP_DATA)/sector_earnings_signal.json: 财报季信号 per Shenwan L2 sector (好消息涨不动; config/sector_earnings_signal.yaml; plan 35)
	$(CLI) sector-earnings-signal --out $(APP_DATA)

sector-monitor:   ## write $(APP_DATA)/sector_monitor.json: 行业监控 (70 城房价, 销售简报, 合同负债, 减值, 版号, 获利盘, 实际波动率; config/sector_monitors.yaml; plan 31)
	$(CLI) sector-monitor --out $(APP_DATA)

buyback-events:   ## write $(APP_DATA)/buybacks.json (large new plans, the book's events; plan 23 ph6) and buyback_monitor.json (market-wide 回购 / 增持; plan 32)
	$(CLI) buyback-events --out $(APP_DATA)

margin-panel:     ## write $(APP_DATA)/margin/<code>.json: 融资融券 series and forced-liquidation ladder per stock (plan 15 ph7m)
	$(CLI) margin-panel --out $(APP_DATA)

futures-monitor:  ## write $(APP_DATA)/futures_monitor.json from fut_daily (config/futures_monitor.yaml; plan 15 ph7i, D-145)
	$(CLI) futures-monitor --out $(APP_DATA)

MACRO_DATASETS :=cn_cpi,cn_ppi,cn_pmi,cn_m,sf_month
macro-monitor:    ## refresh CPI / PPI / PMI / M1-M2 / 社融 (one call each), then write $(APP_DATA)/macro_monitor.json (plan 15 ph7h, D-143)
	$(CLI) download --datasets $(MACRO_DATASETS) --no-progress
	$(CLI) compact --datasets $(MACRO_DATASETS)
	$(CLI) macro-monitor --out $(APP_DATA)

holdings-risk:    ## value config/local.positions.yaml, decompose its risk, write $(APP_DATA)/holdings_risk.json + lake history (D-132)
	$(CLI) holdings-risk --out $(APP_DATA)
	-$(MAKE) notify

holdings-risk-data: ## holdings-risk without the iMessage notify (update-all step, plan 38)
	$(CLI) holdings-risk --out $(APP_DATA)

etf-cta:          ## refresh the last 14 days of fund NAVs (premium guard), then write $(APP_DATA)/etf_cta.json from config/etf_cta.yaml (plan 27, D-160); after etf-proxy
	$(CLI) download --datasets fund_nav --start $$(date -v-14d +%Y%m%d)
	$(CLI) compact --datasets fund_nav
	$(CLI) etf-cta --out $(APP_DATA)

update-all:       ## every daily update in order (config/update_all.yaml; plan 38, D-181): continues past a failed step, skips its dependents, records meta/task_log + $(APP_DATA)/task_status.json. ARGS="--only a,b | --from step | --dry-run | --with-report"
	$(CLI) update-all --out $(APP_DATA) $(ARGS)

track-daily:      ## what the weekday 06:00 launchd job runs: update-all (plan 38)
	$(CLI) update-all --out $(APP_DATA) --trigger launchd $(ARGS)

TRACK_PLIST := $(HOME)/Library/LaunchAgents/com.quantcn.daily-track.plist
TRACK_LOG := $(HOME)/Library/Logs/quant_cn-daily-track.log
track-install:    ## install the weekday 06:00 launchd job (after the China close in US Eastern time) that runs make track-daily (log in ~/Library/Logs)
	sed -e "s|@REPO@|$(CURDIR)|g" -e "s|@PATH@|$(dir $(shell command -v uv)):/opt/homebrew/bin:/usr/bin:/bin|g" -e "s|@LOG@|$(TRACK_LOG)|g" scripts/launchd/daily_track.plist.template > $(TRACK_PLIST)
	-launchctl bootout gui/$$(id -u) $(TRACK_PLIST) 2>/dev/null
	launchctl bootstrap gui/$$(id -u) $(TRACK_PLIST)
	@echo "installed $(TRACK_PLIST); log $(TRACK_LOG)"

track-uninstall:  ## unload the launchd job and delete its plist
	-launchctl bootout gui/$$(id -u) $(TRACK_PLIST) 2>/dev/null
	/bin/rm -f "$(TRACK_PLIST)"

morning-report:   ## send the 持仓监测 and 机会清单 e-mails (DRY=1 writes the HTML into APP_DATA instead)
	$(CLI) morning-report --data $(APP_DATA) $(if $(DRY),--dry-run --out $(APP_DATA))

REPORT_PLIST := $(HOME)/Library/LaunchAgents/com.quantcn.morning-report.plist
REPORT_LOG := $(HOME)/Library/Logs/quant_cn-morning-report.log
report-install:   ## install the weekday 08:00 launchd job that runs make morning-report (log in ~/Library/Logs)
	sed -e "s|@REPO@|$(CURDIR)|g" -e "s|@PATH@|$(dir $(shell command -v uv)):/opt/homebrew/bin:/usr/bin:/bin|g" -e "s|@LOG@|$(REPORT_LOG)|g" scripts/launchd/morning_report.plist.template > $(REPORT_PLIST)
	-launchctl bootout gui/$$(id -u) $(REPORT_PLIST) 2>/dev/null
	launchctl bootstrap gui/$$(id -u) $(REPORT_PLIST)
	@echo "installed $(REPORT_PLIST); log $(REPORT_LOG)"

report-uninstall: ## unload the morning-report launchd job (the plist file stays; delete it by hand if wanted)
	-launchctl bootout gui/$$(id -u) $(REPORT_PLIST) 2>/dev/null
	@echo "unloaded; plist left at $(REPORT_PLIST)"

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
