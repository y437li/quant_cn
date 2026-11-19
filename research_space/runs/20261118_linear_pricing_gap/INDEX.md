# 20261118_linear_pricing_gap

Is the gap between the market cap and a consensus-based value with fading growth (线性定价与市场定价的差) a factor? Monthly test 2019-01 → 2026-11. Logged in `research_space/RESEARCH_LOG.md` (2026-11-18).

| File | Purpose |
|---|---|
| `pricing_gap_factor.py` | month-end panel: consensus FY1–FY3 (report_rc, 90 days, latest per broker), value with growth fading ×0.7 for 7 years and exit PE 15 at 9% (`--alt`: ×0.5, PE 20); gap = log(mv / value); rank IC, deciles, Fama-MacBeth and residual IC net of forward / trailing EP, growth, size, reversal, momentum, turnover; Newey-West t; writes the panel to the lake's meta/runs/research/20261118_linear_pricing_gap |
| `compare_controls.py` | IC of the gap next to forward EP, trailing EP, PEG and the controls; the gap of the 2026 tech leaders on 2026-06-30 |
| `cheap_side.py` | the cheap side: decile excess vs the covered universe (fwd20 / fwd60, non-overlapping for 60d), cheapest decile by year, industry mix, industry-neutral (within L1) deciles, current cheapest names ≥ 100亿 |
| `long_short.py` | monthly long-short: raw deciles, industry-neutral (within L1) 10% legs, and with the long leg excluding FY1 consensus cuts > 10% over 90 days; annualised return, vol, Sharpe, drawdown, turnover, net of 0.3% per unit of turnover, by year |
| `nonlinear_use.py` | nonlinear use of the industry-neutral gap: 20-bin shape, double sorts with momentum / reversal / turnover / size / growth, RetailGauge from 2023, avoid / add rules, large caps (top 40% size) |
| `incremental_value.py` | inside the dear (gi > 0.8) or cheap (gi ≤ 0.2) tail: excess of names meeting a second condition minus those not, t over months; all and large caps |
| `neutral_compare.py` | long-short under no / industry / industry + size neutralisation (residual on L1 dummies and log size), equal and market-cap weight, all and large caps; net of costs, by year |
| `ls_costs.py` | long-short under 0.3 / 0.6 / 1.0% per unit of turnover and 0 / 6 / 10% a year short borrow, industry and industry + size neutral, all and large caps |
| `score_complement.py` | does pricing_gap add to the six score factors (derived.features, processed values)? correlations, score vs score + pricing_gap (IC, decile LS), Fama-MacBeth net of the six, veto inside the score's top quintile; all and large caps |
| `campaign_acceptance.py` | FACTOR_TESTING_DESIGN §6 criteria 1-3 (FactorAcceptance, 20 sessions) on the campaign's IC_TEST, with the score / pricing_gap lines |
| `record_trials.py` | appends the 12 research variants of the pricing gap to the campaign TrialLog (idempotent) |
| `neutral_by_factor.py` | quintile long-short of reversal_1m, pricing_gap, dividend_yield, turnover_60d, momentum_12_1 by neutralisation (none / industry / industry + size), long and short legs, turnover, net Sharpe |
| `current_ranks.py` | current 20 cheapest and dearest by pricing_gap among stocks >= 100亿: premium over consensus value, industry percentile, forward PE, FY1 -> FY2 growth, brokers, 1-month return |
| `basket_history.py` | monthly 20-stock cheapest / dearest baskets (>= 100亿) since 2019: excess, t, hit, Sharpe, by year, last months; the holdings' current percentile |
| `name_paths.py` | 2026 month-end path of pricing_gap for named stocks: percentile among >= 100亿 and premium over the consensus value |
