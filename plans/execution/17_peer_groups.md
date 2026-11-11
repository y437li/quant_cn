# 17 — Peer groups from labeled evidence

| | |
|---|---|
| Status | approved 2026-11-11 (user: "两个都批准，先做plan 18第一阶段"); queued after plan 18 phase 1 |
| Owner | user (approve) / agent (build) |
| Created | 2026-11-11 |
| Notion | pending |
| Decisions | D-123 (proposed), D-099, D-102, D-118, D-122 |
| Depends on plans | 12 (taxonomy, applications, ProductMatcher), 13 (valuation comparables) |

## Goal
Every A-share company has a ranked list of stage-level peers, each with the evidence behind it, and belongs to a named peer group that replaces Shenwan L3 in every peer comparison (margin rank, pricing power, moat, cycle clock).

## Scope
- In:
  - Pair signals: revenue-weighted product cosine (fina_mainbz_p → taxonomy products), broker comparables (plan 13 valuations, 3,813 pairs), competitors named in annual reports (applications), archetype + variant (D-118 business modes), shared named customers / suppliers; chain-stage relation (supplier / customer edges, taxonomy `upstream_of`) as a penalty.
  - Weights in `config/peers.yaml`; scoring, clustering (scipy, no new dependency), group names from the dominant taxonomy product.
  - Evaluation against held-out broker pairs and against the SW L3 baseline.
  - Takes over `GraphQuery.peers` from plan 12 ph6; output tables `derived/peers/{pairs, groups, members}.parquet`.
- Out: point-in-time peer history (one snapshot from FY2025 annual + reports to date, so not for backtests before 2026); new LLM extraction of documents; app UI beyond showing the reasons (plan 15).

## Phases

| # | Phase | Deliverable | Done criterion | Depends on | Status |
|---|---|---|---|---|---|
| 1 | Pair evidence | `PeerEvidenceBuilder` reads the labeled outputs and the lake and writes `derived/peers/pairs.parquet`: one row per (a, b, signal) with value and source refs (doc ids, quote pages). The product cosine moves from `build_market_view.py` into the class | Contract tests pass. Product cosine for 10 named companies equals the prototype's `co/*.json` peers. Row counts per signal reported | — | todo |
| 2 | Scoring + evaluation | `PeerScorer` (weights from `config/peers.yaml`, chain-stage penalty, top-k per company with reasons) and `PeerEvaluator` (hold out broker pairs named in ≥ 2 reports; recall@10 for combined, product-only and SW L3) | Combined recall@10 beats both baselines on the hold-out (numbers in the Log). Weights fixed before the final hold-out run | 1 | todo |
| 3 | Groups | `PeerGrouper`: average-linkage clustering on 1 − score within each chain stage, size bounds from config; group named by dominant product node; companies with weak evidence fall back to SW L3 and are flagged `fallback` | Every listed company has a group or a `fallback` flag. The user checks peers and groups of 10 named companies (宁德时代, 牧原, 立讯, 茅台, 中国平安, 中际旭创, 万华, 海天, 迈瑞, 比亚迪) | 2 | todo |
| 4 | Disputed pairs (LLM) | `PeerAdjudicator` (Ark, D-122) for pairs where signals disagree strongly (e.g. high product cosine but supplier edge, or broker comparable with no product overlap); reply quote-checked against the evidence passed in | Disputed pairs counted before and after; 30 adjudications spot-checked by Opus with ≥ 85% agreement | 3 | todo |
| 5 | Wire in | `PeerStep` (pipeline) writes the tables in `make curate`; `build_market_view.py` `peer_group()` reads `derived/peers/members.parquet`; GM rank, pricing power and moat comparisons switch to peer groups | View rebuilt; a diff report lists companies whose pricing-power or moat label changed vs SW L3. `make check` passes. Registry and INDEX current | 3 (4 optional) | todo |

## Classes

| Class | Action (new / extend / reuse) | Package | Phase |
|---|---|---|---|
| `PeerEvidenceBuilder` | new | `quant_cn.industry_graph` (L4) | 1 |
| `PeerScorer` | new | `quant_cn.industry_graph` | 2 |
| `PeerEvaluator` | new | `quant_cn.industry_graph` | 2 |
| `PeerGrouper` | new | `quant_cn.industry_graph` | 3 |
| `PeerAdjudicator` | new (uses `BaseLlmClient`, `QuoteChecker`) | `quant_cn.industry_graph` | 4 |
| `PeerStep` | new (`BaseStep`) | `quant_cn.pipeline` (L6) | 5 |
| `ProductTaxonomy`, `ProductMatcher`, `QuoteChecker`, `DeepSeekClient` | reuse | industry_graph / data_loading | 1, 4 |
| `PeersConfig` | extend `core.Config` (new `peers` section) | `quant_cn.core` | 2 |

## Risks
- Labeled outputs live in `meta/runs/*/*.jsonl` (prototype runs), not in derived tables; phase 1 reads them through one loader so the source can switch to plan 15 ph2's `derived/graph` without changing the scorer.
- Product mapping errors put equipment makers next to their customers (e.g. 豪森智能 next to 宁德时代): the chain-stage penalty and phase 4 target this; measured in phase 2.
- Broker comparables are both a signal and the hold-out: the hold-out pairs are removed from the evidence before scoring.
- Snapshot, not PIT: using groups in factor backtests before 2026 would leak; `members.parquet` carries `as_of` and the factor layer must not join it historically.
- Conglomerates (several unrelated segments) fit no single group: allow membership in up to 2 groups, weighted by revenue share.

## Open questions
- Recall@10 bar for phase 2: proposed "beats SW L3 by ≥ 10 points"; the user may set an absolute number.
- Group size bounds: proposed 5–40 companies.
- Should HK / US listed comparables that brokers name (e.g. LG 新能源) be kept as reference peers outside the A-share groups?

## Log

| Date | Phase | Change |
|---|---|---|
| 2026-11-11 | — | drafted at the user's request ("可不可以基于我们打标后的内容进行分类" → "可以，写计划吧"); 宁德时代 example: product cosine and broker comparables agree on 国轩高科 and 亿纬锂能, product cosine alone adds an equipment maker |
| 2026-11-11 | — | coverage of 5,676 companies: product cosine ≥ 0.5 peer 83%, business mode 94%, any broker report in 12 months 41%, broker-named comparables 17%; ≥ 2 of (product, broker, competitor) 14%; none of the three 13% (SW L3 fallback) |
| 2026-11-11 | — | approved (user: "两个都批准，先做plan 18第一阶段") |
