"""Market-wide chain view data (plan 12 phase 4 output, prototype view). Reads the lake staging outputs:
FY2025 annual parse (top-5 tables, sections), DeepSeek applications (annual + 2026H1), DeepSeek broker
valuations, Tushare main-business mix, Shenwan membership; writes next to this file:
  view_data.json  -- taxonomy + one light record per company (revenue mix, product ids, company links)
  co/<sw_l1>.json -- per-sector company detail, loaded by the page on demand
Company names in documents are resolved to listed companies by full name, short name, or full name
without the legal suffix; anything else stays an external name."""
import json
import re
from collections import defaultdict
from pathlib import Path

import duckdb
import yaml

from quant_cn.industry_graph.product_matcher import ProductMatcher
from quant_cn.industry_graph.product_taxonomy import ProductTaxonomy

HERE = Path(__file__).parent
REPO = HERE.parents[2]
LAKE = Path("/Volumes/Treasury/quant_cn_lake")
REF = LAKE / "curated" / "reference"
SKIP = re.compile(r"^(产品|合计|其他业务|主营业务|小计)$")
ADJUST = re.compile(r"抵消|抵减|调整|^合计")
ELIM = re.compile(r"抵消|抵减")
SUFFIX = re.compile(r"(股份有限公司|有限责任公司|有限公司|集团|股份)$")
QUICK = ["002714.SZ", "300498.SZ", "002130.SZ", "000895.SZ", "300750.SZ", "601138.SH", "600519.SH", "300308.SZ"]


def load_taxonomy():
    nodes, edges, sectors = {}, [], {}
    for f in sorted((REPO / "config/industry_chain").glob("*.yaml")):
        doc = yaml.safe_load(f.read_text()) or {}
        sec = doc.get("sector") or {}
        if sec:
            sectors[str(sec["sw_l1"])] = sec["name"]
        for n in doc.get("nodes", []):
            nodes.setdefault(n["id"], {"id": n["id"], "t": n["type"], "n": str(n["name"]), "en": n.get("name_en"),
                                       "p": n.get("parent"), "s": n.get("segment"), "k": n.get("kind"),
                                       "imp": n.get("import_dependence"), "al": [str(a) for a in n.get("aliases", [])],
                                       "sec": str(sec.get("sw_l1", "")) or None})
        edges += [[e[0], e[1], e[2]] for e in doc.get("edges", []) if isinstance(e, list) and len(e) == 3]
    return nodes, [e for e in edges if e[0] in nodes and e[2] in nodes], sectors


nodes, edges, sectors = load_taxonomy()
products = [(i, str(lbl)) for i, n in nodes.items() if n["t"] == "product" for lbl in [n["n"], *n["al"]]]
matcher = ProductMatcher(ProductTaxonomy(REPO / "config/industry_chain"))


def match_product(item):
    best, best_len = None, 0
    clean = re.sub(r"[（(].*?[)）]|及|与|和", "", item)
    for pid, label in products:
        if len(label) >= 2 and (label in clean or (len(clean) >= 3 and clean in label)) and len(label) > best_len:
            best, best_len = pid, len(label)
    return best


# --- companies ---
l1_code = dict(duckdb.sql(f"SELECT index_code, industry_code FROM '{REF}/index_classify.parquet' WHERE level = 'L1'").fetchall())
sw_code = dict(duckdb.sql(f"SELECT index_code, industry_code FROM '{REF}/index_classify.parquet'").fetchall())
members = {}
for ts, name, l1, l2, l3c, l3 in duckdb.sql(f"""SELECT ts_code, name, l1_code, l2_code, l3_code, l3_name FROM '{REF}/index_member_all.parquet'
        WHERE out_date IS NULL OR out_date = ''""").fetchall():
    members[ts] = {"code": ts, "name": name, "l1": l1_code.get(l1, "other"), "l3": l3,
                   "sw": [c for c in (sw_code.get(l2), sw_code.get(l3c)) if c]}
for ts, name in duckdb.sql(f"SELECT ts_code, name FROM '{REF}/stock_basic.parquet'").fetchall():
    members.setdefault(ts, {"code": ts, "name": name, "l1": "other", "l3": None})
by6 = {ts[:6]: ts for ts in members}
names = {}
for ts, full in duckdb.sql(f"SELECT ts_code, com_name FROM '{REF}/stock_company.parquet'").fetchall():
    if ts in members and full:
        names[full] = ts
        names.setdefault(SUFFIX.sub("", full), ts)
for ts, m in members.items():
    names.setdefault(m["name"].replace(" ", ""), ts)


SHORT = sorted(((m["name"].replace(" ", ""), ts) for ts, m in members.items() if len(m["name"]) >= 3 and "ST" not in m["name"]),
               key=lambda x: -len(x[0]))
group_hits = set()


def resolve(name):
    """Listed company for a document name: exact full / short name, or a subsidiary whose name starts with
    a listed short name of 3+ characters (比亚迪汽车工业有限公司 -> 比亚迪), marked in group_hits."""
    if not name:
        return None
    n = re.sub(r"\s+|[（(].*?[)）]$", "", name)
    hit = names.get(n) or names.get(SUFFIX.sub("", n))
    if hit:
        return hit
    for short, ts in SHORT:
        if n.startswith(short) and len(n) > len(short):
            group_hits.add(name)
            return ts
    return None


# --- revenue mix (Tushare main business by product, FY2025) ---
rows = defaultdict(list)
for ts, item, sales, profit in duckdb.sql(f"""SELECT ts_code, bz_item, bz_sales, bz_profit
        FROM read_parquet('{LAKE}/curated/documents/fina_mainbz_p/**/*.parquet')
        WHERE end_date = '20251231' AND bz_sales IS NOT NULL""").fetchall():
    rows[ts].append((item, sales, profit))
revenue, elims = {}, {}
for ts, rs in rows.items():
    total = max((s for _, s, _ in rs), default=0) or 1
    seen, out = set(), []
    names_in = {i for i, _, _ in rs}
    sw = members.get(ts, {}).get("sw", [])
    for item, s, p in rs:
        if item in seen or SKIP.match(item) or ADJUST.search(item) or (s >= total * 0.999 and len(rs) > 1):
            continue
        if re.split(r"[：:]", item)[0] in names_in and re.search(r"[：:]", item):
            continue  # a sub-line of a reported parent line (利息净收入：利息支出：...): counted in the parent
        seen.add(item)
        found = matcher.find_matches(item, sw)
        how = "generic" if matcher.is_generic(item) else (found[0].how if found else "none")
        out.append({"item": item, "sales": s, "pct": round(100 * s / total, 2),
                    "gm": round(100 * (p or 0) / s, 1) if s else None, "pids": [m.node_id for m in found], "how": how})
    revenue[ts] = sorted(out, key=lambda r: -r["pct"])
    elims[ts] = [{"item": i, "sales": s, "pct": round(100 * s / total, 2)} for i, s, _ in rs if ELIM.search(i)]

# --- annual parse (rules) ---
parse = {}
for code, n_pages, share, sec, cust, supp in duckdb.sql(f"""SELECT code, n_pages, chapter_share, sections, customers, suppliers
        FROM '{LAKE}/meta/runs/parse/annual_fy2025.parquet' WHERE error IS NULL""").fetchall():
    if code in by6:
        parse[by6[code]] = (n_pages, share, json.loads(sec), json.loads(cust), json.loads(supp))

# --- DeepSeek applications (annual first; semiannual adds counterparties) ---
apps, parties = {}, defaultdict(list)
app_file = LAKE / "meta/runs/applications/applications.jsonl"
for line in app_file.read_text().splitlines():
    r = json.loads(line)
    ts = by6.get(r["code"])
    if not ts or "error" in r:
        continue
    src = "2025年报" if r["doc_type"] == "annual" else "2026半年报"
    if r["doc_type"] == "annual" or ts not in apps:
        apps[ts] = {"lines": r["lines"], "types": r["customer_types"], "src": src, "pages": r["pages"]}
    for cp in r["counterparties"]:
        parties[ts].append({**cp, "src": src, "code": resolve(cp["name"])})

# --- quarterly notes (DeepSeek on Q1/Q3 notes; rule-kept operating reasons otherwise) ---
quarterly = defaultdict(list)
q_file = LAKE / "meta/runs/quarterly/quarterly_notes.jsonl"
for line in (q_file.read_text().splitlines() if q_file.exists() else []):
    r = json.loads(line)
    ts = by6.get(r["code"])
    if ts and r.get("items"):
        quarterly[ts] += [{**i, "period": r["period"]} for i in r["items"]]

# --- broker valuations (latest 3 per company) ---
vals = defaultdict(list)
for line in (LAKE / "meta/runs/valuation/valuations.jsonl").read_text().splitlines():
    r = json.loads(line)
    ts = by6.get(r.get("code") or "")
    if ts and "error" not in r:
        vals[ts].append({"org": r["org"], "date": r["date"], "title": r["title"], "valuation": {
            k: r.get(k) for k in ("rating", "target_price", "methods", "forecasts", "comparables", "assumptions", "logic")}})
for ts in vals:
    vals[ts] = sorted(vals[ts], key=lambda v: v["date"], reverse=True)[:3]
    for v in vals[ts]:
        tp = v["valuation"]["target_price"]
        if tp is not None and not isinstance(tp, dict):
            v["valuation"]["target_price"] = {"value": tp, "currency": ""}

# --- what brokers track and how they value, by product node and by Shenwan L3 (fallback) ---
METRIC_SYN = {"营收": "收入", "营业收入": "收入", "收入增速": "收入增速", "营收增速": "收入增速", "营收同比增速": "收入增速",
              "收入增长率": "收入增速", "综合毛利率": "毛利率", "均价": "单价", "销售均价": "单价", "价格": "单价",
              "出货量": "销量/出货量", "销量": "销量/出货量", "归母净利率": "净利率"}
METHOD_SYN = {"EV_EBITDA": "EV/EBITDA", "P/EV": "PEV", "EV_SALES": "EV/Sales"}


def new_stat():
    return {"reports": set(), "methods": defaultdict(int), "implied": defaultdict(list), "target": [], "pb": [],
            "metrics": defaultdict(int), "loss": set(), "bare": set()}


prod_stat, ind_stat = defaultdict(new_stat), defaultdict(new_stat)
item_pid = {ts: {r["item"]: r["pids"][0] for r in rev if r["pids"]} for ts, rev in revenue.items()}
for line in (LAKE / "meta/runs/valuation/valuations.jsonl").read_text().splitlines():
    r = json.loads(line)
    ts = by6.get(r.get("code") or "")
    if not ts or "error" in r:
        continue
    rev = revenue.get(ts, [])
    main = next((x["pids"][0] for x in rev if x["pids"] and x["pct"] >= 40), None)  # single-business companies

    def pid_for(label):
        if not label or label == "整体":
            return main
        found = matcher.find_matches(label, members.get(ts, {}).get("sw", []))
        return item_pid.get(ts, {}).get(label) or (found[0].node_id if found else None) or main

    targets = [ind_stat[members[ts]["l3"] or "?"]] if ts in members else []
    fcs = sorted((f for f in r.get("forecasts") or [] if isinstance(f.get("net_profit_bn"), (int, float))), key=lambda f: str(f.get("year")))
    loss = bool(fcs) and fcs[0]["net_profit_bn"] < 0  # nearest forecast year is a loss
    bare = not any(m.get("multiple") is not None for m in r.get("methods") or [])  # rating only, no multiple
    for st in targets + [prod_stat[p] for p in {pid_for(None)} if p]:
        st["reports"].add(r["doc_id"])
        if loss:
            st["loss"].add(r["doc_id"])
        if bare:
            st["bare"].add(r["doc_id"])
    for mth in r.get("methods") or []:
        name = METHOD_SYN.get(str(mth.get("method")).upper(), str(mth.get("method")).upper())
        pid = pid_for(mth.get("applied_to"))
        for st in targets + ([prod_stat[pid]] if pid else []):
            st["reports"].add(r["doc_id"])
            st["methods"][name] += 1
            mult = mth.get("multiple")
            if name == "PE" and isinstance(mult, (int, float)) and 0 < mult < 300:
                if mth.get("multiple_kind") == "implied_at_price" and mth.get("base_year"):
                    st["implied"][str(mth["base_year"])].append(mult)
                elif mth.get("multiple_kind") == "target":
                    st["target"].append(mult)
            if name == "PB" and isinstance(mult, (int, float)) and 0 < mult < 50:
                st["pb"].append(mult)
    for asm in r.get("assumptions") or []:
        metric = METRIC_SYN.get(asm.get("metric") or "", asm.get("metric") or "")
        if not metric:
            continue
        pid = pid_for(asm.get("segment"))
        for st in targets + ([prod_stat[pid]] if pid else []):
            st["reports"].add(r["doc_id"])
            st["metrics"][metric] += 1


def summarize(st):
    med = lambda xs: round(sorted(xs)[len(xs) // 2], 1) if xs else None
    by_year = {y: (med(v), len(v)) for y, v in sorted(st["implied"].items()) if y.endswith("E") and len(v) >= 2}
    n = max(len(st["reports"]), 1)
    return {"n": len(st["reports"]), "methods": sorted(st["methods"].items(), key=lambda x: -x[1])[:5],
            "pe_by_year": by_year, "pe_implied": (by_year.get("2026E") or (None, 0))[0],
            "pe_implied_n": (by_year.get("2026E") or (None, 0))[1],
            "pb": med(st["pb"]), "pb_n": len(st["pb"]),
            "loss_share": round(len(st["loss"]) / n, 2), "bare_share": round(len(st["bare"]) / n, 2),
            "pe_target": med(st["target"]), "pe_target_n": len(st["target"]),
            "metrics": sorted(st["metrics"].items(), key=lambda x: -x[1])[:8]}


broker_prod = {pid: summarize(st) for pid, st in prod_stat.items() if len(st["reports"]) >= 3}
broker_ind = {l3: summarize(st) for l3, st in ind_stat.items() if len(st["reports"]) >= 3}
print("products with a broker view:", len(broker_prod))

# --- business model (BUSINESS_MODEL_DESIGN §1, §4.1, §4.2): archetype defaults, lifecycle, cycle clock ---
# Prototype rules on FY2023-FY2025 consolidated annual statements (all public by 2026-04-30, PIT-safe now).
bm_cfg = yaml.safe_load((REPO / "config/business_models.yaml").read_text()) or {}
archetypes = {k: {f: v.get(f) for f in ("name", "revenue_formula", "drivers", "pricing", "pass_through", "profit_hinge",
                                       "cycle_signals", "moat_types", "valuation_methods")}
              | {"variants": {x["id"]: {"name": x["name"], "description": x.get("description", "")} for x in v.get("variants") or []}}
              for k, v in (bm_cfg.get("archetypes") or {}).items()}
bm_l3 = {str(k): v for k, v in (bm_cfg.get("sw_l3") or {}).items()}
FUND = LAKE / "curated" / "fundamentals"
YEARS = ("20231231", "20241231", "20251231")


def latest(table, cols):
    q = f"""SELECT ts_code, end_date, {cols} FROM read_parquet('{FUND}/{table}/**/*.parquet')
            WHERE end_date IN {YEARS} {"AND report_type = '1'" if table != "fina_indicator" else ""}
            QUALIFY row_number() OVER (PARTITION BY ts_code, end_date ORDER BY ann_date DESC, update_flag DESC) = 1"""
    out = defaultdict(dict)
    for row in duckdb.sql(q).fetchall():
        out[row[0]][row[1][:4]] = row[2:]
    return out


cf = latest("cashflow", "c_pay_acq_const_fiolta, depr_fa_coga_dpba, n_cashflow_act")
bs = latest("balancesheet", "cip, fix_assets, accounts_receiv, contract_liab, adv_receipts")
inc = latest("income", "revenue, oper_cost")
roic = defaultdict(dict)
for ts, end, v in duckdb.sql(f"""SELECT ts_code, end_date, roic FROM read_parquet('{FUND}/fina_indicator/**/*.parquet')
        WHERE end_date LIKE '%1231' AND end_date >= '20190101'
        QUALIFY row_number() OVER (PARTITION BY ts_code, end_date ORDER BY ann_date DESC) = 1""").fetchall():
    if v is not None:
        roic[ts][end[:4]] = v


def growth(a, b):
    return (a / b - 1) if a is not None and b not in (None, 0) and b > 0 else None


fin = {}
for ts in members:
    c25, c24 = cf.get(ts, {}).get("2025"), cf.get(ts, {}).get("2024")
    i25, i24 = inc.get(ts, {}).get("2025"), inc.get(ts, {}).get("2024")
    b25, b24 = bs.get(ts, {}).get("2025"), bs.get(ts, {}).get("2024")
    if not (c25 and i25):
        continue
    capex, dep, ocf = c25
    fin[ts] = {"capex": capex, "dep": dep, "fcf": (ocf - capex) if ocf is not None and capex is not None else None,
               "capex_dep": round(capex / dep, 2) if capex and dep else None,
               "capex_g": growth(capex, c24[0] if c24 else None),
               "rev_g": growth(i25[0], i24[0] if i24 else None),
               "gm": (1 - i25[1] / i25[0]) if i25[0] and i25[1] is not None else None,
               "gm24": (1 - i24[1] / i24[0]) if i24 and i24[0] and i24[1] is not None else None,
               "cip_g": growth(b25[0], b24[0] if b24 else None) if b25 else None,
               "rev": i25[0], "rev24": i24[0] if i24 else None, "capex24": c24[0] if c24 else None}


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 2] if xs else None


l3_rev_g = {l3: median(fin[ts]["rev_g"] for ts in members if members[ts]["l3"] == l3 and ts in fin)
            for l3 in {m["l3"] for m in members.values()}}


def classify_life(f, peer_g):
    """§4.1: 扩张期 / 运营期 / 收缩期 from capex vs depreciation, CIP and growth vs the L3 median."""
    if f["capex_dep"] is None:
        return "数据不足"
    ahead = f["rev_g"] is not None and peer_g is not None and f["rev_g"] > peer_g
    if f["capex_dep"] > 1.5 and ((f["cip_g"] or 0) > 0 or ahead):
        return "扩张期"
    if f["capex_dep"] < 0.8 and not ahead:
        return "收缩期"
    return "运营期"


def classify_clock(demand, margin_pp, capex):
    """§4.2 table: demand = revenue growth, margin = gross-margin change in pp, capex = capex growth."""
    if demand is None or margin_pp is None:
        return "数据不足"
    up, down = demand > 0.05, demand < 0
    if up and margin_pp > 0.5:
        return "扩张" if capex is not None and capex > 0.1 else "复苏"
    if up:
        return "扩张"
    if margin_pp < -0.5 and capex is not None and capex > 0.05:
        return "过剩"
    if down and margin_pp < -0.5:
        return "出清"
    return "过渡"


def aggregate(codes):
    rs = [fin[t] for t in codes if t in fin and fin[t]["rev"] and fin[t]["rev24"]]
    if len(rs) < 3:
        return None
    r25, r24 = sum(f["rev"] for f in rs), sum(f["rev24"] for f in rs)
    gm25 = sum(f["gm"] * f["rev"] for f in rs if f["gm"] is not None) / r25
    gm24 = sum(f["gm24"] * f["rev24"] for f in rs if f["gm24"] is not None) / r24
    cx = [f for f in rs if f["capex"] and f["capex24"]]
    capex_g = (sum(f["capex"] for f in cx) / sum(f["capex24"] for f in cx) - 1) if cx else None
    d, m = r25 / r24 - 1, (gm25 - gm24) * 100
    return {"n": len(rs), "demand": round(d, 3), "margin_pp": round(m, 1),
            "capex": round(capex_g, 3) if capex_g is not None else None, "phase": classify_clock(d, m, capex_g)}


clock_l3 = {}
for l3 in {m["l3"] for m in members.values() if m["l3"]}:
    v = aggregate([ts for ts in members if members[ts]["l3"] == l3])
    if v:
        clock_l3[l3] = v
# product level: revenue and margin of the mapped 主营构成 lines (FY2024 vs FY2025), capex of the producers
prod_rows = defaultdict(lambda: {"r25": 0.0, "r24": 0.0, "p25": 0.0, "p24": 0.0, "makers": set()})
prev = defaultdict(dict)
for ts, item, sales, profit in duckdb.sql(f"""SELECT ts_code, bz_item, bz_sales, bz_profit
        FROM read_parquet('{LAKE}/curated/documents/fina_mainbz_p/**/*.parquet')
        WHERE end_date = '20241231' AND bz_sales > 0""").fetchall():
    prev[ts][item] = (sales, profit or 0)
for ts, rev in revenue.items():
    for r in rev:
        old = prev.get(ts, {}).get(r["item"])
        if not r["pids"] or not old or r["how"] == "sector" or r["sales"] <= 0:
            continue
        share = 1 / len(r["pids"])
        for pid in r["pids"]:
            x = prod_rows[pid]
            x["r25"] += r["sales"] * share
            x["p25"] += r["sales"] * (r["gm"] or 0) / 100 * share
            x["r24"] += old[0] * share
            x["p24"] += old[1] * share
            x["makers"].add(ts)
clock_prod = {}
for pid, x in prod_rows.items():
    if len(x["makers"]) < 3 or x["r24"] <= 0:
        continue
    d, m = x["r25"] / x["r24"] - 1, (x["p25"] / x["r25"] - x["p24"] / x["r24"]) * 100
    cx = [fin[t] for t in x["makers"] if t in fin and fin[t]["capex"] and fin[t]["capex24"]]
    capex_g = (sum(f["capex"] for f in cx) / sum(f["capex24"] for f in cx) - 1) if cx else None
    clock_prod[pid] = {"n": len(x["makers"]), "demand": round(d, 3), "margin_pp": round(m, 1),
                       "capex": round(capex_g, 3) if capex_g is not None else None, "phase": classify_clock(d, m, capex_g)}
print("cycle clock:", len(clock_l3), "L3,", len(clock_prod), "products")


def business_card(ts):
    m = members.get(ts, {})
    l3code = (m.get("sw") or [None, None])[-1]
    f = fin.get(ts)
    r = roic.get(ts, {})
    gms = [fin[t]["gm"] for t in members if members[t]["l3"] == m.get("l3") and t in fin and fin[t]["gm"] is not None]
    return {"l3code": l3code, "default": bm_l3.get(str(l3code)),
            "life": {"label": classify_life(f, l3_rev_g.get(m.get("l3"))), **{k: f[k] for k in ("capex_dep", "cip_g", "rev_g", "fcf", "capex")},
                     "peer_rev_g": l3_rev_g.get(m.get("l3"))} if f else {"label": "数据不足"},
            "roic": dict(sorted(r.items())), "gm": f["gm"] if f else None, "peer_gm": median(gms)}


# --- synthesized broker views (BrokerViewSynthesizer, plan 13 ph4): product / L3 in views.json, company in shards ---
doc_meta = {}
for line in (LAKE / "meta/runs/valuation/valuations.jsonl").read_text().splitlines():
    r = json.loads(line)
    ts = by6.get(r.get("code") or "")
    doc_meta[r["doc_id"]] = f"{r.get('org') or ''} {r.get('date') or ''}《{r.get('title') or ''}》{'（' + members[ts]['name'] + '）' if ts in members else ''}"
views = {"product": {}, "industry": {}, "company": {}}
v_file = LAKE / "meta/runs/valuation/broker_views.jsonl"
for line in (v_file.read_text().splitlines() if v_file.exists() else []):
    r = json.loads(line)
    if "error" in r:
        continue
    r["refs"] = {k: doc_meta.get(d, d) for k, d in r.get("refs", {}).items()}
    views[r["scope"]][r["id"]] = {k: r[k] for k in ("summary", "method_consensus", "multiple_range", "points", "refs", "n_reports", "n_sent")}
print("broker views:", {k: len(v) for k, v in views.items()})
(HERE / "views.json").write_text(json.dumps({"product": views["product"], "industry": views["industry"]},
                                            ensure_ascii=False, separators=(",", ":")))

# --- industry-specific KPIs (config/sector_kpis.yaml, D-106) ---
kpi_cfg = (yaml.safe_load((REPO / "config/sector_kpis.yaml").read_text()) or {}).get("sectors", {})
kpis = {str(k): {"kpis": [{f: x.get(f) for f in ("id", "name", "unit", "freq", "definition", "origin", "tier")} for x in v.get("kpis") or []],
                 "groups": [{"name": g["name"], "sw": [str(c) for c in g.get("sw", [])],
                             "kpis": [{f: x.get(f) for f in ("id", "name", "unit", "freq", "definition", "origin", "tier")} for x in g.get("kpis") or []]}
                            for g in v.get("groups") or []]}
        for k, v in kpi_cfg.items()}

# --- financial table FY2023-FY2025 (D-117): statement lines and ratios to revenue ---
FIN_COLS = ("total_revenue", "revenue", "oper_cost", "biz_tax_surchg", "sell_exp", "admin_exp", "rd_exp", "fin_exp",
            "assets_impair_loss", "credit_impa_loss", "invest_income", "operate_profit", "total_profit", "income_tax",
            "n_income", "n_income_attr_p")
fin_table = defaultdict(dict)
for row in duckdb.sql(f"""SELECT ts_code, end_date, {", ".join(FIN_COLS)}
        FROM read_parquet('{FUND}/income/**/*.parquet', union_by_name = true)
        WHERE end_date IN {YEARS} AND report_type = '1'
        QUALIFY row_number() OVER (PARTITION BY ts_code, end_date ORDER BY f_ann_date DESC, update_flag DESC) = 1""").fetchall():
    v = dict(zip(FIN_COLS, row[2:]))
    rev = v["total_revenue"] or v["revenue"]
    out = {k: v[k] for k in FIN_COLS if v[k] is not None}
    if rev:
        if v["oper_cost"] is not None:
            out["gross_profit"] = v["revenue"] - v["oper_cost"] if v["revenue"] else None
            out["gm"] = round((v["revenue"] - v["oper_cost"]) / v["revenue"], 4) if v["revenue"] else None
        for k in ("sell_exp", "admin_exp", "rd_exp", "fin_exp", "n_income_attr_p", "operate_profit"):
            if v[k] is not None:
                out[k + "_r"] = round(v[k] / rev, 4)
        exp = [v[k] for k in ("sell_exp", "admin_exp", "rd_exp", "fin_exp") if v[k] is not None]
        if exp:
            out["opex_r"] = round(sum(exp) / rev, 4)
    fin_table[row[0]][row[1][:4]] = out

# --- quarterly table (single quarters from YTD statements), last 8 quarters with YoY (user, 2026-11-08) ---
Q_COLS = ("total_revenue", "revenue", "oper_cost", "sell_exp", "admin_exp", "rd_exp", "fin_exp", "operate_profit", "n_income_attr_p")
ytd = defaultdict(dict)
for row in duckdb.sql(f"""SELECT ts_code, end_date, {", ".join(Q_COLS)}
        FROM read_parquet('{FUND}/income/**/*.parquet', union_by_name = true)
        WHERE end_date >= '20220101' AND report_type = '1'
        QUALIFY row_number() OVER (PARTITION BY ts_code, end_date ORDER BY f_ann_date DESC, update_flag DESC) = 1""").fetchall():
    ytd[row[0]][row[1]] = dict(zip(Q_COLS, row[2:]))


def single_quarters(per):
    """YTD -> single quarter: Q1 = YTD(Q1); Qn = YTD(Qn) - YTD(Qn-1) of the same year; None when a period is missing."""
    out = {}
    for end in sorted(per):
        y, md = end[:4], end[4:]
        prev = {"0331": None, "0630": "0331", "0930": "0630", "1231": "0930"}.get(md, "x")
        if prev == "x":
            continue
        cur, base = per[end], (per.get(y + prev) if prev else {})
        if prev and base is None:
            continue
        q = {}
        for k in Q_COLS:
            a, b = cur.get(k), (base.get(k) if base else 0)
            q[k] = (a - (b or 0)) if a is not None and (not prev or b is not None) else None
        out[f"{y}Q{({'0331': 1, '0630': 2, '0930': 3, '1231': 4})[md]}"] = q
    return out


quarters = {}
for ts, per in ytd.items():
    qs = single_quarters(per)
    rows = []
    for key in sorted(qs)[-8:]:
        q = qs[key]
        rev = q["total_revenue"] or q["revenue"]
        last = qs.get(f"{int(key[:4]) - 1}{key[4:]}")
        r = {"q": key, "rev": rev, "np": q["n_income_attr_p"], "op": q["operate_profit"]}
        if rev:
            if q["revenue"] and q["oper_cost"] is not None:
                r["gm"] = round((q["revenue"] - q["oper_cost"]) / q["revenue"], 4)
            for k in ("sell_exp", "admin_exp", "rd_exp", "fin_exp"):
                if q[k] is not None:
                    r[k + "_r"] = round(q[k] / rev, 4)
            if q["n_income_attr_p"] is not None:
                r["npm"] = round(q["n_income_attr_p"] / rev, 4)
        if last:
            lrev = last["total_revenue"] or last["revenue"]
            if rev and lrev and lrev > 0:
                r["rev_yoy"] = round(rev / lrev - 1, 4)
            if q["n_income_attr_p"] is not None and last["n_income_attr_p"]:
                r["np_yoy"] = round((q["n_income_attr_p"] - last["n_income_attr_p"]) / abs(last["n_income_attr_p"]), 4)
        rows.append(r)
    quarters[ts] = rows

# --- DuPont path: FY2019-FY2025 and the latest period annualised (ROE, asset turnover, net margin, leverage) ---
dupont = defaultdict(list)
ANNUALISE = {"0331": 4, "0630": 2, "0930": 4 / 3, "1231": 1}
latest_end = {}
for ts, end, roe_v, at, npm, d2a in duckdb.sql(f"""SELECT ts_code, end_date, roe, assets_turn, netprofit_margin, debt_to_assets
        FROM read_parquet('{FUND}/fina_indicator/**/*.parquet') WHERE end_date >= '20190101'
        QUALIFY row_number() OVER (PARTITION BY ts_code, end_date ORDER BY ann_date DESC) = 1
        ORDER BY ts_code, end_date""").fetchall():
    if roe_v is None or at is None:
        continue
    f = ANNUALISE[end[4:]]
    point = {"p": end[:4] if end.endswith("1231") else f"{end[:4]}Q{({'0331': 1, '0630': 2, '0930': 3})[end[4:]]}年化",
             "roe": round(roe_v * f, 2), "at": round(at * f, 3), "npm": round(npm, 2) if npm is not None else None,
             "lev": round(1 / (1 - d2a / 100), 2) if d2a is not None and d2a < 100 else None, "end": end}
    if end.endswith("1231"):
        dupont[ts].append(point)
    latest_end[ts] = point
for ts, pt in latest_end.items():
    if not pt["end"].endswith("1231"):
        dupont[ts].append(pt)
def dupont_flags(x):
    """Driver and warning of one DuPont point (user, 2026-11-08: "净利润低也能有高ROE吗？").
    driver: margin (npm >= 15% and turnover < 1) / turnover (>= 1.2 and multiplier < 3) / leverage (multiplier >= 3)
    / mixed. flag: thin (multiplier >= 5: equity too small, ROE distorted), gap (npm x turnover x multiplier differs
    from ROE by more than 30% or in sign: equity moved a lot within the year), or ''."""
    npm, at, lev, roe = x.get("npm"), x["at"], x.get("lev"), x["roe"]
    if npm is None or lev is None:
        return "mixed", ""
    driver = "margin" if npm >= 15 and at < 1 else "turnover" if at >= 1.2 and lev < 3 else "leverage" if lev >= 3 else "mixed"
    prod = npm * at * lev
    gap = (prod * roe < 0) or (abs(roe) > 2 and abs(prod - roe) > 0.3 * abs(roe))
    return driver, "thin" if lev >= 5 else "gap" if gap else ""


for pts in dupont.values():
    for x in pts:
        x["driver"], x["flag"] = dupont_flags(x)
dupont_all = defaultdict(list)  # per period: [turnover, ROE, code, L1, L3, driver, flag]
latest_q = max((x["end"] for pts in dupont.values() for x in pts if not x["end"].endswith("1231")), default=None)
for ts, pts in dupont.items():
    if ts not in members:
        continue
    for x in pts:
        if len(x["p"]) == 4:
            dupont_all[x["p"]].append([x["at"], x["roe"], ts, members[ts]["l1"], members[ts]["l3"], x["driver"], x["flag"]])
        elif x["end"] == latest_q:  # e.g. "2026Q3": only companies that already reported that quarter
            dupont_all[x["p"].replace("年化", "")].append([x["at"], x["roe"], ts, members[ts]["l1"], members[ts]["l3"], x["driver"], x["flag"]])
dupont_l3 = defaultdict(list)  # FY2025 cloud of the L3 peers
for ts, pts in dupont.items():
    fy = next((x for x in pts if x["p"] == "2025"), None)
    if fy and ts in members and members[ts]["l3"] and -60 < fy["roe"] < 80 and fy["at"] < 5:
        dupont_l3[members[ts]["l3"]].append([fy["at"], fy["roe"], ts])

# --- segment leaders: top makers per node by revenue on the mapped lines (A-share listed only) ---
node_sales = defaultdict(lambda: defaultdict(float))
for ts, rev in revenue.items():
    for r in rev:  # sector-fallback lines map to a segment id, so they count at segment level only
        if not (r["sales"] and r["sales"] > 0 and r["pids"]) or "退市" in members.get(ts, {}).get("name", ""):
            continue
        if r["how"] == "sector" and r["pct"] < 40:  # a fallback line counts only when it is the main business
            continue
        for pid in r["pids"]:
            node_sales[pid][ts] += r["sales"] / len(r["pids"])
seg_sales = defaultdict(lambda: defaultdict(float))
for pid, by in node_sales.items():
    seg = nodes.get(pid, {}).get("s") if nodes.get(pid, {}).get("t") == "product" else (pid if nodes.get(pid, {}).get("t") == "segment" else None)
    if seg:
        for ts, v in by.items():
            seg_sales[seg][ts] += v
merged = {pid: by for pid, by in node_sales.items() if nodes.get(pid, {}).get("t") != "segment"} | dict(seg_sales)
leaders = {}
for pid, by in merged.items():
    total = sum(by.values())
    top = sorted(by.items(), key=lambda x: -x[1])[:5]
    leaders[pid] = {"n": len(by), "total": round(total), "top": [{"code": ts, "name": members.get(ts, {}).get("name", ts),
                                                                    "sales": round(v), "share": round(v / total, 4)} for ts, v in top]}
print("quarters:", len(quarters), "dupont:", len(dupont), "leaders:", len(leaders))

# --- pricing power (BUSINESS_MODEL_DESIGN §4.5, D-118): six measured signals + one text signal -------------
import statistics

q_gm = {}  # ts -> [(quarter, single-quarter GM)] from 2022
for ts, per in ytd.items():
    out = []
    for key, q in sorted(single_quarters(per).items()):
        if q["revenue"] and q["revenue"] > 0 and q["oper_cost"] is not None:
            out.append((key, (q["revenue"] - q["oper_cost"]) / q["revenue"]))
    q_gm[ts] = out[-12:]
mp_cfg = (yaml.safe_load((REPO / "config/material_prices.yaml").read_text()) or {}).get("materials", {})
contracts = sorted({c for cs in mp_cfg.values() for c in cs})
fut_q = defaultdict(dict)  # contract -> quarter -> mean close
for code, q, px in duckdb.sql(f"""SELECT ts_code, substr(trade_date, 1, 4) || 'Q' || ((CAST(substr(trade_date, 5, 2) AS INT) + 2) // 3), avg(close)
        FROM read_parquet('{LAKE}/curated/fut_daily/**/*.parquet') WHERE ts_code IN {tuple(contracts)} AND trade_date >= '20220101'
        GROUP BY 1, 2""").fetchall():
    if px:  # quarters without a close are skipped
        fut_q[code][q] = px


def material_index(mat):
    """Quarterly index of a material: mean of its contracts, each normalised to its own mean."""
    series = []
    for c in mp_cfg.get(mat, []):
        q = fut_q.get(c, {})
        if len(q) >= 6:
            m = statistics.mean(q.values())
            series.append({k: v / m for k, v in q.items()})
    if not series:
        return {}
    keys = set.intersection(*(set(x) for x in series))
    return {k: statistics.mean(x[k] for x in series) for k in keys}


mat_index = {m: material_index(m) for m in mp_cfg}
uses = defaultdict(set)
for a, r, b in edges:
    if r == "uses_material":
        uses[a].add(b)


def basket(weights):
    """Weighted quarterly index from {material: weight}."""
    parts = [(w, mat_index[m]) for m, w in weights.items() if mat_index.get(m) and w > 0]
    if not parts:
        return {}
    keys = set.intersection(*(set(x) for _, x in parts))
    tot = sum(w for w, _ in parts)
    return {k: sum(w * x[k] for w, x in parts) / tot for k in keys}


def slope(gm_series, index):
    """OLS slope of ΔGM (pp) on Δindex (%) over consecutive quarters; None below 6 pairs or with flat costs."""
    pairs = []
    for (k0, g0), (k1, g1) in zip(gm_series, gm_series[1:]):
        if k0 in index and k1 in index and index[k0] > 0:
            pairs.append(((index[k1] / index[k0] - 1) * 100, (g1 - g0) * 100))
    if len(pairs) < 6:
        return None, 0
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    if statistics.pstdev(xs) < 3:  # input prices hardly moved: pass-through cannot be measured
        return None, len(pairs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return round(b, 3), len(pairs)


gm_std = {ts: statistics.pstdev([g for _, g in v]) for ts, v in q_gm.items() if len(v) >= 8}
l3_members = defaultdict(list)
for ts, m in members.items():
    if m["l3"]:
        l3_members[m["l3"]].append(ts)
mkt_std = sorted(gm_std.values())
modes = {}
m_file = LAKE / "meta/runs/business/business_modes.jsonl"
for line in (m_file.read_text().splitlines() if m_file.exists() else []):
    r = json.loads(line)
    if "error" not in r and r["code"] in by6:
        modes[by6[r["code"]]] = r
# own selling-price moves only (cost moves such as 采购价格下降 are not pricing actions)
SELL = r"(售价|销售价格|销售均价|产品价格|出厂价|产品均价)"
PRICE_UP = re.compile(rf"提价|涨价|{SELL}\S{{0,6}}(上调|上涨|提高|提升)")
PRICE_DOWN = re.compile(rf"降价|{SELL}\S{{0,6}}(下降|下调|下跌|降低)")


l1_members = defaultdict(list)
for _ts, _m in members.items():
    l1_members[_m["l1"]].append(_ts)


def peer_group(ts):
    """The company's Shenwan L3, or its L1 when the L3 has fewer than 5 companies with statements."""
    m = members.get(ts, {})
    l3 = [t for t in l3_members.get(m.get("l3"), []) if t in fin]
    return (l3, "同三级行业") if len(l3) >= 5 else ([t for t in l1_members.get(m.get("l1"), []) if t in fin], "同一级行业")


def pricing_signals(ts):
    """Each signal: (key, 'maker' | 'taker' | None, detail). None = measured but neutral; missing = not measurable."""
    m, f = members.get(ts, {}), fin.get(ts)
    out = []
    group, gname = peer_group(ts)
    peers = [t for t in group if fin[t]["gm"] is not None]
    if f and f["gm"] is not None and len(peers) >= 5:
        rank = sum(fin[t]["gm"] < f["gm"] for t in peers) / len(peers)
        out.append(("P1", "maker" if rank >= 2 / 3 else "taker" if rank <= 1 / 3 else None, f"毛利率 {f['gm']:.1%}，{gname}分位 {rank:.0%}"))
    if ts in gm_std:
        pstd = [gm_std[t] for t in group if t in gm_std]
        med = statistics.median(pstd) if len(pstd) >= 5 else None
        if med:
            r = gm_std[ts] / med if med else 1
            out.append(("P2", "maker" if r < 0.7 else "taker" if r > 1.3 else None, f"单季毛利率波动 {gm_std[ts] * 100:.1f}pp，同行中位 {med * 100:.1f}pp"))
    rev = revenue.get(ts, [])
    w_in, w_out = defaultdict(float), defaultdict(float)
    for r in rev:
        for pid in r["pids"]:
            for mat in uses.get(pid, ()):
                w_in[mat] += max(r["pct"], 0) / len(r["pids"])
            if pid in mp_cfg:
                w_out[pid] += max(r["pct"], 0) / len(r["pids"])
    for mat in list(w_in):  # an input that is also the company's own product is an output (P4), not a cost
        if mat in w_out:
            del w_in[mat]
    if w_in and ts in q_gm:
        b, n = slope(q_gm[ts], basket(w_in))
        if b is not None:  # clearly positive = margins rise with input prices: output-driven, no vote
            out.append(("P3", "maker" if -0.1 < b < 0.3 else "taker" if b < -0.3 else None, f"原料价每涨 1%，毛利率变动 {b:+.2f}pp（{n} 个季度，原料：{'、'.join(nodes[x]['n'] for x in list(w_in)[:3] if x in nodes)}）"))
    if w_out and ts in q_gm:
        b, n = slope(q_gm[ts], basket(w_out))
        if b is not None and b > 0.15:
            out.append(("P4", "taker", f"售价每涨 1%，毛利率 +{b:.2f}pp：利润随市场价（{n} 个季度）"))
    # nodes with 5+ listed makers; a small share is not evidence of no pricing power (niches), so P5 only votes maker
    big = {p for r in rev for p in r["pids"] if leaders.get(p, {}).get("n", 0) >= 5}
    shares = [ld["share"] for pid in big for ld in leaders[pid]["top"] if ld["code"] == ts]
    if big:
        top = max(shares, default=0)
        out.append(("P5", "maker" if top >= 0.3 else None, f"最大细分份额 {top:.0%}" if top else "不在任何细分前五"))
    phases = {clock_prod[p]["phase"] for r in rev for p in r["pids"] if p in clock_prod}
    if f and f["gm"] is not None and f["gm24"] is not None and phases & {"过剩", "出清"}:
        d = (f["gm"] - f["gm24"]) * 100
        pd = [(fin[t]["gm"] - fin[t]["gm24"]) * 100 for t in group if fin[t]["gm"] is not None and fin[t]["gm24"] is not None]
        med = statistics.median(pd) if len(pd) >= 5 else None
        if med is not None:
            out.append(("P6", "maker" if d >= -1 and d > med else "taker" if d < med - 2 else None, f"产品处于{'/'.join(sorted(phases & {'过剩', '出清'}))}，毛利率 {d:+.1f}pp（同行中位 {med:+.1f}pp）"))
    t_votes, t_detail = [], []
    md = modes.get(ts) or {}
    pt, pr = (md.get("pass_through") or {}).get("value"), (md.get("pricing") or {}).get("value")
    if pt in ("full",) or pr == "brand":
        t_votes.append("maker"); t_detail.append(f"年报：{'成本可传导' if pt == 'full' else '品牌定价'}")
    if pt == "none" or pr == "market":
        t_votes.append("taker"); t_detail.append(f"年报：{'成本不能传导' if pt == 'none' else '随市场定价'}")
    for a in md.get("price_actions") or []:
        t_votes.append("maker" if a["direction"] == "up" else "taker" if a["direction"] == "down" else None)
        t_detail.append(f"年报：{a['item']}{'提价' if a['direction'] == 'up' else '降价' if a['direction'] == 'down' else '价格维持'}{a.get('magnitude') or ''}")
    for q in quarterly.get(ts, []):
        txt = q.get("summary", "")
        if PRICE_UP.search(txt):
            t_votes.append("maker"); t_detail.append(f"{q['period']}季报：{txt[:30]}")
        elif PRICE_DOWN.search(txt):
            t_votes.append("taker"); t_detail.append(f"{q['period']}季报：{txt[:30]}")
    t_votes = [v for v in t_votes if v]
    if t_votes:
        mk, tk = t_votes.count("maker"), t_votes.count("taker")
        out.append(("T1", "maker" if mk > tk else "taker" if tk > mk else None, "；".join(t_detail[:3])))
    return out


def pricing_label(signals):
    """Graded label (user, 2026-11-08: "可以判断一下不确定的"): score = maker votes - taker votes.
    >= +2 maker, <= -2 taker, +1 lean_maker, -1 lean_taker, 0 middle; fewer than 2 measured signals insufficient.
    Confidence: high when 4+ signals and no contrary vote, medium when 3+ signals, low otherwise."""
    makers = sum(v == "maker" for _, v, _ in signals)
    takers = sum(v == "taker" for _, v, _ in signals)
    if len(signals) < 2:
        return "insufficient", "low"
    score = makers - takers
    label = "maker" if score >= 2 else "taker" if score <= -2 else "lean_maker" if score == 1 else "lean_taker" if score == -1 else "middle"
    conf = "high" if len(signals) >= 4 and min(makers, takers) == 0 and label in ("maker", "taker") else "medium" if len(signals) >= 3 else "low"
    return label, conf


sigs = bm_cfg.get("signatures") or {}
vol_cut = (mkt_std[len(mkt_std) // 3], mkt_std[2 * len(mkt_std) // 3]) if mkt_std else (0, 0)


def archetype_check(ts, label, signals):
    """§4b.7: measured company data against the archetype's expected signatures."""
    l3code = (members.get(ts, {}).get("sw") or [None])[-1]
    default = bm_l3.get(str(l3code))
    sig = sigs.get(default["archetype"]) if default else None
    if not sig:
        return {"status": "insufficient", "checks": []}
    checks, f = [], fin.get(ts)
    if f and f["gm"] is not None:
        lo, hi = sig["gm"]
        checks.append(("毛利率", lo <= f["gm"] <= hi, f"{f['gm']:.1%}，预期 {lo:.0%}–{hi:.0%}"))
    if ts in gm_std:
        band = "low" if gm_std[ts] <= vol_cut[0] else "high" if gm_std[ts] >= vol_cut[1] else "mid"
        checks.append(("毛利率波动", band == sig["gm_vol"] or "mid" in (band, sig["gm_vol"]), f"{ {'low': '低', 'mid': '中', 'high': '高'}[band]}，预期{ {'low': '低', 'mid': '中', 'high': '高'}[sig['gm_vol']]}"))
    if label != "insufficient":
        zh = {"maker": "定价者", "middle": "中间", "taker": "跟价者", "lean_maker": "偏定价者", "lean_taker": "偏跟价者"}
        base = {"lean_maker": "maker", "lean_taker": "taker"}.get(label, label)
        checks.append(("定价权", base in sig["pricing"] or (label.startswith("lean") and "middle" in sig["pricing"]), f"{zh[label]}，预期{'或'.join(zh[x] for x in sig['pricing'])}"))
    at = next((x["at"] for x in dupont.get(ts, []) if x["p"] == "2025"), None)
    if at is not None:
        lo, hi = sig["turnover"]
        checks.append(("资产周转率", lo <= at <= hi, f"{at}，预期 {lo}–{hi}"))
    if sig.get("output_beta") == "positive":
        checks.append(("利润随售价", any(k == "P4" for k, _, _ in signals), "毛利率随售价变动" if any(k == "P4" for k, _, _ in signals) else "未测到毛利率随售价变动"))
    bad = [c for c in checks if not c[1]]
    status = "insufficient" if len(checks) < 3 else "inconsistent" if len(bad) >= 2 else "partial" if bad else "consistent"
    md = modes.get(ts) or {}
    return {"status": status, "archetype": default["archetype"], "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in checks],
            "variant": (md.get("variant") or {}).get("value"), "variant_quote": ((md.get("variant") or {}).get("evidence") or {}).get("quote"),
            "proposed_variant": md.get("proposed_variant"),
            "pricing_text": (md.get("pricing") or {}).get("value"), "pass_through_text": (md.get("pass_through") or {}).get("value")}


pricing_power, arche_checks = {}, {}
for ts in members:
    sg = pricing_signals(ts)
    lab, conf = pricing_label(sg)
    pricing_power[ts] = {"label": lab, "confidence": conf, "signals": [{"key": k, "vote": v, "detail": d} for k, v, d in sg]}
    arche_checks[ts] = archetype_check(ts, lab, sg)
adj_file = LAKE / "meta/runs/business/pricing_adjudication.jsonl"
for line in (adj_file.read_text().splitlines() if adj_file.exists() else []):  # DeepSeek verdicts (D-118)
    r = json.loads(line)
    if "error" in r or r["code"] not in pricing_power:
        continue
    pricing_power[r["code"]]["llm"] = {k: r[k] for k in ("label", "confidence", "reasons", "evidence")}
    arche_checks[r["code"]]["llm"] = {k: r[k] for k in ("archetype_ok", "archetype", "variant_note")}
from collections import Counter
print("pricing power:", Counter(v["label"] for v in pricing_power.values()), "archetype check:", Counter(v["status"] for v in arche_checks.values()))

# --- moat (BUSINESS_MODEL_DESIGN §4.4): claimed (DeepSeek, 核心竞争力) vs proven (ROIC, margins, share) ---------
SUBTYPES = [("franchise", re.compile(r"特许经营|经营权|收费权|专营权|独家经营")),
            ("license", re.compile(r"牌照|资质|许可证|准入|批文|注册证|认证")),
            ("patent", re.compile(r"专利|发明|知识产权|核心技术|技术壁垒|自主研发")),
            ("brand", re.compile(r"品牌|商标|老字号|驰名|知名度"))]


def claim_subtype(c):
    """Finer label of a claim from its own words (no LLM): franchise / license / patent / brand, else the type."""
    text = f"{c.get('claim', '')} {c.get('evidence', {}).get('quote', '')}"
    return next((k for k, rx in SUBTYPES if rx.search(text)), c["type"])


def rd_ratio(ts):
    f = fin_table.get(ts, {}).get("2025", {})
    return f.get("rd_exp_r")


def chain_position(ts):
    """Bargaining position in the chain (user, 2026-11-09: "产业链定价权"): advances from customers, receivables, and
    dependence on the top-5 customers / suppliers. strong / weak / neutral with the numbers."""
    b = bs.get(ts, {}).get("2025")
    f = fin.get(ts)
    if not b or not f or not f["rev"]:
        return None
    _cip, _fa, ar, cl, adv = b
    rev = f["rev"]
    adv_r = ((cl or 0) + (adv or 0)) / rev
    ar_r = (ar or 0) / rev
    p = parse.get(ts)
    cust = p[3]["total_pct"] if p else None
    supp = p[4]["total_pct"] if p else None
    detail = f"预收/合同负债占营收 {adv_r:.0%}，应收占营收 {ar_r:.0%}，前五客户 {'—' if cust is None else f'{cust:.0f}%'}，前五供应商 {'—' if supp is None else f'{supp:.0f}%'}"
    l3code = (members.get(ts, {}).get("sw") or [None])[-1]
    arche = (bm_l3.get(str(l3code)) or {}).get("archetype")
    concentrated = cust is not None and cust >= 50 and arche not in ("A7", "A12")  # utilities sell to the grid by design
    if concentrated or ar_r >= 0.4:
        return "weak", detail
    if (adv_r >= 0.10 or ar_r <= 0.05) and (cust is None or cust < 30):
        return "strong", detail
    return "neutral", detail

moat_claims = {}
mc_file = LAKE / "meta/runs/business/moat_claims.jsonl"
for line in (mc_file.read_text().splitlines() if mc_file.exists() else []):
    r = json.loads(line)
    if "error" not in r and r["code"] in by6:
        moat_claims[by6[r["code"]]] = r
ROIC_FLOOR, ROIC_WIDE = 8.0, 15.0  # cost-of-capital proxy; a wide moat earns well above it


def roic_series(ts):
    return [roic[ts][y] for y in sorted(roic.get(ts, {}))][-6:]


def roic_mean(ts):
    xs = roic_series(ts)
    return statistics.mean(xs) if xs else None


def gm_rank(ts):
    group, _ = peer_group(ts)
    f = fin.get(ts)
    peers = [t for t in group if fin[t]["gm"] is not None]
    if not f or f["gm"] is None or len(peers) < 5:
        return None
    return sum(fin[t]["gm"] < f["gm"] for t in peers) / len(peers)


def gm_stability(ts):
    group, _ = peer_group(ts)
    pstd = [gm_std[t] for t in group if t in gm_std]
    if ts not in gm_std or len(pstd) < 5 or not statistics.median(pstd):
        return None
    return gm_std[ts] / statistics.median(pstd)  # < 1 = steadier than peers


def top_share(ts):
    big = {p for r in revenue.get(ts, []) for p in r["pids"] if leaders.get(p, {}).get("n", 0) >= 5}
    return max((ld["share"] for pid in big for ld in leaders[pid]["top"] if ld["code"] == ts), default=0.0)


def peer_roic(ts):
    group, _ = peer_group(ts)
    xs = [m for m in (roic_mean(t) for t in group) if m is not None]
    return statistics.median(xs) if len(xs) >= 5 else None


def test_claim(kind, ts, ctx):
    """True / False / None (untestable) for one claimed moat type, with the numbers used."""
    rank, stab, share, rm, prm, above = ctx["rank"], ctx["stab"], ctx["share"], ctx["roic"], ctx["peer_roic"], ctx["above"]
    if kind == "intangible" and rank is not None and stab is not None:
        return rank >= 2 / 3 and stab < 1.0, f"毛利率同行分位 {rank:.0%}，波动为同行的 {stab:.1f} 倍"
    if kind == "cost" and rm is not None and prm is not None:
        ok = (rank is None or rank < 2 / 3) and rm >= prm + 3 or share >= 0.3
        return ok, f"ROIC 均值 {rm:.1f}%（同行中位 {prm:.1f}%），毛利率分位 {'—' if rank is None else f'{rank:.0%}'}，份额 {share:.0%}"
    if kind == "switching" and stab is not None and rm is not None:
        return stab < 0.8 and rm >= 10, f"毛利率波动为同行的 {stab:.1f} 倍，ROIC 均值 {rm:.1f}%"
    if kind == "network" and rm is not None:
        return rm >= ROIC_WIDE and share >= 0.3, f"ROIC 均值 {rm:.1f}%，份额 {share:.0%}"
    if kind == "efficient_scale" and rm is not None:
        return share >= 0.3 and above >= 4, f"份额 {share:.0%}，近 6 年 ROIC ≥8% 的年数 {above}"
    return None, "数据不足以检验"


def moat_card(ts):
    xs = roic_series(ts)
    if len(xs) < 4:
        return {"width": "insufficient", "trend": None, "roic": dict(sorted(roic.get(ts, {}).items())), "claims": []}
    above = sum(x >= ROIC_FLOOR for x in xs)
    wide_years = sum(x >= ROIC_WIDE for x in xs)
    trend = statistics.mean(xs[-3:]) - statistics.mean(xs[:3])
    ctx = {"rank": gm_rank(ts), "stab": gm_stability(ts), "share": top_share(ts), "roic": statistics.mean(xs),
           "peer_roic": peer_roic(ts), "above": above}
    edge = (ctx["rank"] is not None and ctx["rank"] >= 0.5) or ctx["share"] >= 0.3
    width = "wide" if wide_years >= 5 and edge and trend > -5 else "narrow" if above >= 4 else "none"
    mc = moat_claims.get(ts) or {}
    claims = []
    rstd = statistics.pstdev(xs)
    peer_rstd = [statistics.pstdev(roic_series(t)) for t in peer_group(ts)[0] if len(roic_series(t)) >= 4]
    rd = rd_ratio(ts)
    peer_rd = [r for r in (rd_ratio(t) for t in peer_group(ts)[0]) if r is not None]
    for c in mc.get("claims", []):
        sub = claim_subtype(c)
        if sub == "patent" and rd is not None and len(peer_rd) >= 5 and ctx["rank"] is not None:
            med = statistics.median(peer_rd)
            ok, why = rd >= med and ctx["rank"] >= 0.5, f"研发费用率 {rd:.1%}（同行中位 {med:.1%}），毛利率分位 {ctx['rank']:.0%}"
        elif sub == "license":
            ok, why = above >= 4, f"近 6 年 ROIC ≥8% 的年数 {above}"
        elif sub == "franchise" and len(peer_rstd) >= 5:
            med = statistics.median(peer_rstd)
            ok, why = rstd < med and above >= 4, f"ROIC 波动 {rstd:.1f}pp（同行中位 {med:.1f}pp），≥8% 的年数 {above}"
        else:
            ok, why = test_claim("intangible" if sub == "brand" else c["type"], ts, ctx)
        claims.append({**c, "subtype": sub, "proven": ok, "test": why})
    proven = sorted({c["subtype"] for c in claims if c["proven"]})
    # measured sources, whatever the company claims
    sources = []
    pl = (pricing_power.get(ts) or {}).get("label")
    if pl in ("maker", "lean_maker"):
        sources.append({"key": "pricing_power", "detail": {"maker": "定价者", "lean_maker": "偏定价者"}[pl]})
    firsts = [nodes[pid]["n"] for pid in {p for r in revenue.get(ts, []) for p in r["pids"]}
              if leaders.get(pid, {}).get("n", 0) >= 5 and leaders[pid]["top"][0]["code"] == ts and leaders[pid]["top"][0]["share"] >= 0.3 and pid in nodes]
    if firsts:
        sources.append({"key": "market_share", "detail": f"细分第一（份额 ≥30%）：{'、'.join(firsts[:3])}"})
    cp = chain_position(ts)
    if cp and cp[0] == "strong":
        sources.append({"key": "chain_position", "detail": cp[1]})
    return {"width": width, "trend_pp": round(trend, 1),
            "roic": dict(sorted(roic.get(ts, {}).items())), "above_floor": above, "wide_years": wide_years,
            "gm_rank": ctx["rank"], "gm_stability": ctx["stab"], "share": ctx["share"], "peer_roic": ctx["peer_roic"],
            "claims": claims, "summary": mc.get("summary", ""), "proven_types": proven, "read": bool(mc),
            "sources": sources, "chain_position": cp}


moats = {ts: moat_card(ts) for ts in members}
# trend relative to peers: the market-wide ROIC cycle (high 2020–21, low 2023–25) is not a moat change
for ts, m in moats.items():
    if m.get("trend_pp") is None:
        m["trend"] = None
        continue
    group, _ = peer_group(ts)
    pt = [moats[t]["trend_pp"] for t in group if moats.get(t, {}).get("trend_pp") is not None]
    rel = m["trend_pp"] - (statistics.median(pt) if len(pt) >= 5 else 0.0)
    m["trend_rel_pp"] = round(rel, 1)
    m["trend"] = "widening" if rel >= 3 else "eroding" if rel <= -3 else "stable"
print("moat width:", Counter(v["width"] for v in moats.values()), "trend:", Counter(v["trend"] for v in moats.values()),
      "claims read:", sum(v.get("read", False) for v in moats.values()))

# --- peers: cosine similarity of revenue-weighted product vectors (moved out of the page, APP_STANDARD §1) ---
vectors = {}
for ts, rev in revenue.items():
    v = defaultdict(float)
    for r in rev:
        for pid in r["pids"]:
            v[pid] += max(r["pct"], 0) / len(r["pids"])
    if v:
        vectors[ts] = v
by_pid = defaultdict(set)
for ts, v in vectors.items():
    for pid in v:
        by_pid[pid].add(ts)
norms = {ts: sum(x * x for x in v.values()) ** 0.5 for ts, v in vectors.items()}
peers = {}
for ts, v in vectors.items():
    cands = set().union(*(by_pid[pid] for pid in v)) - {ts}
    scored = []
    for o in cands:
        shared = [pid for pid in v if pid in vectors[o]]
        dot = sum(v[pid] * vectors[o][pid] for pid in shared)
        if norms[ts] and norms[o]:
            scored.append((round(dot / (norms[ts] * norms[o]), 3), o, shared))
    peers[ts] = [{"code": o, "score": sc, "shared": sh} for sc, o, sh in sorted(scored, reverse=True)[:20]]

# --- assemble ---
light, shards, stats = [], defaultdict(dict), defaultdict(int)
for ts, m in members.items():
    rev = revenue.get(ts, [])
    p = parse.get(ts)
    if not rev and not p:
        continue
    n_pages, share, sec, cust, supp = p or (0, 0, {}, {"total_pct": None, "total": None, "consistent": False, "rows": []},
                                            {"total_pct": None, "total": None, "consistent": False, "rows": []})
    links = []
    for table, kind in ((cust, "c"), (supp, "s")):
        for r in table["rows"]:
            r["code"] = None if r["anon"] else resolve(r["name"])
            r["group"] = r["name"] in group_hits
            if r["code"] and r["code"] != ts:
                links.append([r["code"], kind, r["pct"]])
                stats["top5_resolved"] += 1
            stats["top5_named"] += not r["anon"]
    a = apps.get(ts, {"lines": {}, "types": {}, "src": None})
    for r in rev:
        r["apps"] = a["lines"].get(r["item"], [])
        for app in r["apps"]:  # a quote that is mostly a table row of numbers is weak evidence
            q = app["evidence"]["quote"]
            if sum(ch.isdigit() for ch in q) > 0.4 * len(q.replace(" ", "")):
                app["weight"], app["weak"] = "次要", True
    seen, cps = set(), []
    for cp in parties.get(ts, []):
        if cp["role"] == "mention":  # background mentions: counted, not shipped
            stats["mentions"] += 1
            continue
        key = (cp["name"], cp["role"])
        if key in seen:
            continue
        seen.add(key)
        cps.append(cp)
        if cp["code"] and cp["code"] != ts and cp["role"] in ("customer", "supplier", "competitor", "partner"):
            links.append([cp["code"], {"customer": "C", "supplier": "S", "competitor": "P", "partner": "R"}[cp["role"]], None])
            stats["llm_resolved_" + cp["role"]] += 1
    top5 = {r["name"] for t in (cust, supp) for r in t["rows"]}
    named = [{"name": cp["name"], "detail": cp["detail"], "page": cp["evidence"]["page"], "code": cp["code"], "src": cp["src"]}
             for cp in cps if cp["role"] == "customer" and cp["name"] not in top5]
    light.append({"code": ts, "name": m["name"], "l1": m["l1"], "l3": m["l3"], "sw": m.get("sw", []),
                  "revenue": [{k: r[k] for k in ("item", "pct", "gm", "pids", "how")} for r in rev],
                  "cpt": [cust["total_pct"], supp["total_pct"]], "links": links, "llm": bool(a["src"])})
    shards[m["l1"]][ts] = {"source": "2025 年年报" + (f" · DeepSeek 读{a['src']}业务章节" if a["src"] else ""),
                           "pages": n_pages, "sections": sec, "md_share": share, "customers": cust, "suppliers": supp,
                           "named": named, "llm": {"counterparties": cps, "types": a["types"]} if a["src"] else None,
                           "apps": {r["item"]: r["apps"] for r in rev}, "valuations": vals.get(ts, []),
                           "quarterly": quarterly.get(ts, []), "business": business_card(ts),
                           "broker_view": views["company"].get(ts), "peers": peers.get(ts, []), "financials": fin_table.get(ts, {}), "quarters": quarters.get(ts, []), "dupont": dupont.get(ts, []),
                           "pricing_power": pricing_power.get(ts), "archetype_check": arche_checks.get(ts), "moat": moats.get(ts),
                           "regions": [], "eliminations": elims.get(ts, []), "internal": []}
    stats["companies"] += 1
    stats["with_llm"] += bool(a["src"])
    stats["with_products"] += any(r["pids"] for r in rev)

(HERE / "co").mkdir(exist_ok=True)
for sec_code, detail in shards.items():
    (HERE / "co" / f"{sec_code}.json").write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")))
(HERE / "view_data.json").write_text(json.dumps({"nodes": list(nodes.values()), "edges": edges, "sectors": sectors,
                                                 "companies": light, "quick": QUICK,
                                                 "broker_prod": broker_prod, "broker_ind": broker_ind, "kpis": kpis,
                                                 "archetypes": archetypes, "clock_l3": clock_l3, "clock_prod": clock_prod,
                                                 "leaders": leaders, "dupont_all": dupont_all,
                                                 "names": {ts: m["name"] for ts, m in members.items()}}, ensure_ascii=False, separators=(",", ":")))
print(json.dumps(stats, ensure_ascii=False))
print("view_data.json", round((HERE / "view_data.json").stat().st_size / 1e6, 1), "MB;",
      "co/ total", round(sum(f.stat().st_size for f in (HERE / "co").glob("*.json")) / 1e6, 1), "MB")
