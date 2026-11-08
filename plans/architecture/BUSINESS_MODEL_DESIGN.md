# Business model design — how each company makes money, where it is in its cycle, how long it lasts (v0.4, D-112, D-118)

Part of the CompanyCard (D-104), plan 12 phase 6, fed by plans 12 ph4 and 13. Purpose: for every
company, a structured answer to "what drives revenue and profit, who sets the price, who pays, and
what it costs", expressed so that numbers from filings, sector KPIs (D-106) and broker assumptions
(plan 13) plug into the same slots and can be compared across companies of one archetype.

## 1. Archetypes

Every company gets one primary archetype per revenue segment (a conglomerate can have several). The
archetype fixes the revenue-driver formula, the pricing question and the KPIs that matter. Default
mapping from Shenwan L3 in `config/business_models.yaml`; the company's own 经营模式 text can
override it per segment.

| # | Archetype | Revenue driver (segment) | Price set by | Profit hinge | Typical SW L3 |
|---|---|---|---|---|---|
| A1 | Commodity producer | volume × market price | market (price-taker) | unit cost vs price (完全成本) | 生猪养殖, 煤炭开采, 工业金属, 锂, 化工原料 |
| A2 | Processing spread | volume × (output price − input price) | spread between two markets | 加工费 / 价差, utilisation | 炼化, 钢铁, 电解铝, 饲料, 屠宰 |
| A3 | B2B component / material supplier | shipments × ASP × mix | negotiated with concentrated customers; annual price-downs | customer concentration, design wins, mix upgrades | 光模块, PCB, 电池, 汽车零部件, 硅片, 被动元件 |
| A4 | Equipment / project contractor | new orders → backlog → revenue recognised | bid / contract | order intake, backlog cover, gross margin per project | 半导体设备, 电网设备, 工程机械, 建筑, 军工整机 |
| A5 | Consumer brand | volume × price per unit, by channel | brand (price-maker within its tier) | channel mix, price per unit (吨价), marketing ratio | 白酒, 乳品, 调味品, 家电, 服装, 化妆品 |
| A6 | Retail / distribution | stores or GMV × take rate | competitive | same-store growth, gross margin, inventory turns | 超市, 医药流通, 电商, 免税 |
| A7 | Regulated utility / infrastructure | capacity × utilisation hours × regulated tariff | regulator | tariff, fuel cost pass-through, utilisation | 火电, 水电, 燃气, 高速公路, 机场, 港口 |
| A8 | Traffic / unit service | units served × yield | competitive or regulated | load factor, yield, unit cost | 航空, 快递, 航运, 酒店, 旅游 |
| A9 | Software / platform / subscription | users or contracts × ARPU (recurring) + projects | contract | recurring share, retention, R&D ratio | 软件, IT 服务, 游戏, 互联网媒体 |
| A10 | Pharma / biotech portfolio | Σ product sales (+ licensing / milestones) | NRDL / VBP negotiation | pipeline, VBP exposure, licensing income | 化学制药, 生物制品, 中药 |
| A11 | Contract service (CXO, EMS/ODM, foundry) | capacity × utilisation × price per unit | negotiated | utilisation, customer mix | CXO, 晶圆代工, 消费电子组装 |
| A12 | Financial balance sheet | interest-earning assets × NIM + fees − credit cost | market / regulator | NIM, NPL, cost of risk, fee share | 银行, 保险, 证券, 多元金融 |

### 1b. Operating-mode variants (user, 2026-11-07: "每个行业其实他们的商业模式也有不太一样")
Within one archetype, companies run different operating modes. In hog farming, for example, 牧原 is
integrated self-breeding with its own slaughter (asset-heavy), 温氏 is 公司+农户 contract farming
(asset-light, farmer fees as the main cost) and 新希望 is feed plus farming. Each archetype therefore
lists `variants` (integrated / contract, ODM vs own brand, equipment vendor vs EPC, direct vs
distributor, licence vs SaaS vs project, …) with recognisable signals. The SW L3 map gives only the
default archetype and the common variants. The archetype and variant of a company's segment are decided
per company from its own 经营模式 / 主要业务 text (DeepSeek, in the existing business-section call)
and from rule signals: the 分销售模式 table, cost items such as 代养费, asset intensity, customer
concentration. Peer comparison and the cycle clock use archetype + variant, not the SW industry alone.

## 2. CompanyCard.business_model (per company, per period, every field with evidence)

| Block | Content | Main source (rules first, D-103) |
|---|---|---|
| `segments` | per revenue segment: archetype, operating-mode variant, share of revenue, gross margin, taxonomy products | `fina_mainbz`, 营业收入构成 table |
| `driver_tree` | per segment: the archetype formula with each driver's KPI id (D-106), latest value, period, source; e.g. 牧原 生猪: 出栏量 7,800 万头 × 均价 14.9 元/kg − 完全成本 12.1 元/kg | sector KPIs, monthly briefs, broker assumptions (plan 13) |
| `cost_structure` | cost items and their share of 营业成本 (raw materials, labour, depreciation, energy, outsourcing), the top raw materials with their taxonomy material ids | 营业成本构成 table (rules); 主要原材料 text (LLM) |
| `pricing` | who sets the price (market / spread / negotiated / bid / brand / regulated), cost pass-through (full / lagged / none), annual price-downs | 经营模式 text (LLM); archetype default |
| `customers` | B2B / B2C / B2G mix, top-5 concentration, region split, channel split (直销 / 经销 / 线上) | top-5 table, 分地区, 分销售模式 (rules); customer types (D-102) |
| `supply` | top-5 supplier concentration, key inputs and their import dependence | top-5 table, taxonomy `import_dependence` |
| `capital` | asset intensity (fixed assets / revenue), capex / revenue, working-capital days (receivable, inventory, payable) | `fina_indicator` and statements already in the lake |
| `cyclicality` | price exposures: which commodity / market prices move revenue or cost, with sign; demand cycle (end markets) | driver tree + taxonomy end markets |
| `growth` | capacity under construction and start dates, new products, overseas plans | 产能 / 在建工程 sections (rules + LLM) |
| `integration` | internal supply between own segments, integration ratio (D-104) | elimination rows |

## 3. How the parts connect

```
segments ──(archetype)──▶ driver_tree ◀── sector KPIs (D-106: core / broker / disclosed)
    │                          ▲
    │                          └──────── broker assumptions (plan 13: volume, price, margin per segment)
    ├── cost_structure ──▶ taxonomy materials ──▶ commodity prices (cyclicality)
    ├── customers / supply ──▶ graph edges (D-102)
    └── capital, growth, integration
```
A broker's assumption ("2026E 出栏量 8,200 万头") and a monthly brief's actual value both land on the
same driver node, so forecast vs actual and broker dispersion are direct comparisons.

## 4. Stage, cycle, durability, moat (user, 2026-11-07)

Four judgements on top of the business model, each a label plus the signals and evidence behind it.

### 4.1 Company lifecycle: 扩张期 / 运营期 / 收缩期
Rules on PIT statements (lake since 2016), per company and per segment where disclosed:
- 扩张期 (expansion): capex / depreciation > 1.5, 在建工程 (`cip`) growing, capacity under construction
  announced, revenue growth > industry.
- 运营期 (operating): capex ≈ depreciation, stable capacity, free cash flow > 0, payout possible.
- 收缩期 (contraction): capex < depreciation, impairments, capacity closures or asset sales, revenue
  share of industry falling.
Text evidence: 产能 / 在建产能 and 未来发展 sections; IR records.

### 4.2 Cycle clock: where the industry (and product) is
Three signals per industry aggregate and per taxonomy product (product-level from `fina_mainbz`
revenue and margin mapped to nodes, so a booming product is not averaged away inside its SW L3):
demand (revenue growth), profitability (gross-margin change), supply (capex growth); for A1/A2
archetypes also the commodity price and inventory days.

| Phase | Demand | Margin | Capex |
|---|---|---|---|
| 复苏 recovery | ↑ | ↑ | low / falling |
| 扩张 expansion | ↑ | ↑ or flat | ↑ |
| 过剩 overcapacity | flat / ↓ | ↓ | still ↑ |
| 出清 clearing | ↓ | ↓ | ↓ (exits, closures) |

The trajectory (last 8 quarters / 3 years) is drawn as a path on the clock. A company is placed
against its industry (ahead / behind the cycle). Broker industry reports supply the narrative check
("产能出清", "周期底部"): agreement or disagreement between rules and brokers is shown, not resolved.
Prototype FY2025 (2-signal version): PV, polysilicon, lithium = 出清; PCB = 扩张; hog farming
2024 复苏 → 2025 出清 — all plausible; baijiu (revenue −18%) and 通信网络设备 (optical modules mixed
with weak peers) mislabelled, hence the demand signal and the product level.

### 4.3 Durability: will the business still exist in 10 years
Structured signals, then one LLM synthesis with citations (Opus for the final review of a sample):
- Demand: end-market trend (taxonomy end markets × industry growth), technology substitution risk
  (taxonomy `substitute_for` edges, e.g. AEC ↔ optical, sodium-ion ↔ LFP), regulatory exposure
  (VBP, export controls, subsidies), import-substitution tailwind (`import_dependence`).
- Company: cost position in its industry (cost-curve rank where unit cost is disclosed), balance
  sheet (net debt / EBITDA, cash runway), market-share trend, customer concentration risk.
- Output: 高 / 中 / 低 with the three strongest reasons and the main threat.

### 4.4 Moat: what protects the profits, and is it proven
Claimed sources from the annual report's 核心竞争力分析 section (located already) and broker reports,
classified as: cost advantage (scale, resource, process), switching costs (design-in, certification,
B2B qualification), intangibles (brand, licences, patents), network effects, efficient scale
(regulated / local monopoly). Each claim is then tested against numbers:
- ROIC minus a cost-of-capital proxy, persistence over 5+ years (fina_indicator `roic`);
- gross-margin level and stability versus peers (same products / archetype);
- price premium (e.g. 吨价 vs peers), unit-cost advantage, share trend, top-customer stability.
Output: moat type(s), width 宽 / 窄 / 无, `claimed` vs `proven`, and trend (widening / eroding).

### 4.5 Pricing power: price maker or price taker (user, 2026-11-08)
Per company, and per segment where 主营构成 splits it. Six measured signals and one text signal. Every number
is computed in Python on PIT data; the output is a label plus the reasons, never a bare score.

| # | Signal | Source | Maker if | Taker if |
|---|---|---|---|---|
| P1 | Gross-margin level vs peers (same product node, else L3) | fina_mainbz (half-years), income | top tercile | bottom tercile |
| P2 | Gross-margin stability: std of the last 12 single-quarter GMs vs peers | income (single quarters) | below peer median | above peer median |
| P3 | Cost pass-through: slope of ΔGM on Δinput-cost index over 12 quarters. The index is the futures basket of the node's `uses_material` inputs (`config/material_prices.yaml`, new) | income, fut_daily, taxonomy | slope ≈ 0 with cost exposure (passes costs on) | slope clearly < 0 (absorbs costs) |
| P4 | Output-price exposure: slope of ΔGM on Δ own-product price, A1/A2 only | fut_daily / sge | — | slope clearly > 0 (sells at the market price) |
| P5 | Market share in its node (nodes with 5+ listed makers) | leaders (plan 15) | ≥ 30% | — (a small share is neutral: niches can price) |
| P6 | Margin through the cycle: GM change while the node's cycle clock is 过剩/出清 | clock_prod | GM held (Δ ≥ −1 pp) | GM fell more than the peer median |
| T1 | Text: price increases or decreases, 定价方式, 成本传导 statements | quarterly notes (have), annual 经营模式 (DeepSeek, §5 step 3) | 提价 held, cost-plus contracts | 随行就市, 被动降价 |

Output `pricing_power` (graded, user 2026-11-08 "可以判断一下不确定的"): score = maker votes − taker
votes; ≥ +2 `maker`, ≤ −2 `taker`, +1 `lean_maker`, −1 `lean_taker`, 0 `middle`; fewer than 2 measured
signals `insufficient`. Confidence: high (4+ signals, no contrary vote), medium (3+), low. Companies still
`insufficient` or `inconsistent` after the text signal go to a DeepSeek adjudication with all signals and
evidence (cost-confirmed separately). Shown with the 3 strongest reasons and the evidence (numbers, quotes).

## 4b. Cross-cutting rules and further blocks (v0.3)

### 4b.1 Point in time (binding)
Every label and number is stored with the date it became knowable: statements by announcement date
(`f_ann_date`, D-038), annual-report text by its filing date, broker reports by publication date,
monthly briefs by their date. A judgement is recomputed per period and kept as history, never
overwritten, so labels can later serve as factors without look-ahead (FACTOR_TESTING_DESIGN §11).

### 4b.2 Accounting quality (`accounting_quality`)
Flags that discount every other judgement when they fire:
- receivables growth ≫ revenue growth; operating cash flow / net profit < 0.5 over 3 years;
- inventory days rising with falling gross margin; goodwill / equity > 30%; large other receivables;
- frequent restatements (update_flag history), auditor changes, non-standard audit opinions.
Source: lake statements (rules); audit opinion and restatements from announcements.

### 4b.3 Governance and capital allocation (`governance`)
Controller type (SOE central / local / private / foreign), share pledges, insider selling
(`stk_holdertrade`), dividend payout and buybacks, M&A history and goodwill impairments, related-party
transactions (top-5 related shares, D-104), management changes. Question answered: does profit reach
minority shareholders?

### 4b.4 Competitive structure (`competition`)
Per taxonomy product: CR3 / CR5 and HHI of A-share makers by product revenue (fina_mainbz mapped to
nodes), trend over years, number of entrants and exits, price-war signals (industry price falling
while capacity rises). Feeds the cycle clock (过剩 vs 出清) and the moat test (share trend).

### 4b.5 Sensitivity (`sensitivity`)
From the driver tree: profit change for a ±10% move in each driver (product price, key input price,
volume, FX), e.g. hog price for 牧原, copper for cable makers, LME/SHFE prices for A1/A2. Linked to the
lake's price series (futures, macro) so exposures can be updated daily.

### 4b.6 Validation (every label)
Each label type has a stratified hand-check sample (30 companies, user + Opus review) and a recorded
precision; a label type goes live only above its bar (lifecycle / clock ≥ 85%, moat / durability
reviewed as reasoned judgements, not scored). Rule-vs-broker disagreements are kept as a review queue.

### 4b.7 Posterior check of the archetype (user, 2026-11-08: "商业模式有后验结果了吗？")
The archetype and variant are priors (Opus default per SW L3, D-112). Each archetype gets **expected
signatures** in `config/business_models.yaml` (`signatures:`): ranges or directions for GM level, GM
volatility (P2), pass-through (P3/P4), asset turnover, capex/depreciation, customer concentration
(top-5 share), R&D and selling ratios. Example: A1 commodity = volatile GM that follows the output price
(P4 > 0), low pricing power. Brand consumer = GM ≥ 50%, stable, maker.
Per company the check reports `consistent` / `inconsistent` / `insufficient` with the deviating
signatures. Each `inconsistent` goes to a review queue together with the company's own 经营模式 text
(DeepSeek variant reading, §5 step 3). A confirmed mismatch updates the company's label (not the L3
default) and is counted in the label precision of §4b.6.

## 5. Build order

1. `config/business_models.yaml`: the 12 archetypes (formula, drivers as KPI ids, pricing default,
   profit hinges) and the SW L3 → archetype default map (Opus prior, like the taxonomy; user spot-check).
2. Rule extractors for 营业成本构成 and 分销售模式 tables (same machinery as the top-5 parser).
3. One more DeepSeek field set on the 经营模式 / 主要业务 text (pricing, pass-through, channel), added
   to the existing business-section call, so no extra pass over the reports.
4. Lifecycle and cycle clock from PIT statements (rules, free); industry and product level.
5. Accounting quality, governance, competition and sensitivity blocks (rules on lake data).
6. Moat and durability: 核心竞争力 claims (LLM, in the business-section call) tested against
   ROIC, margins and share; final synthesis with citations.
7. Assemble `business_model` in the CompanyCard builder (plan 12 ph6); a 商业模式 tab and a cycle-clock
   chart in the view.

## 6. Open points
- Archetype per segment vs per company: per segment proposed (宁德时代 = A3 batteries + A1 mining).
- Driver values without disclosure (e.g. 牧原 完全成本 is IR-only): taken from IR records or broker
  reports, marked `estimated` with source.
