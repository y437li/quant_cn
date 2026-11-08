"""Prototype data for the industry-chain view (plan 12 phase 6 design): taxonomy + 10 parsed companies.
Writes view_data.json next to this file. Throwaway; production builds this from schema `graph`."""
import glob
import json
import re
import urllib.request
from pathlib import Path

import yaml

from quant_cn.industry_graph.annual_report_parser import AnnualReportParser
from quant_cn.industry_graph.counterparty_table_parser import CounterpartyTableParser
from quant_cn.industry_graph.pdf_text_extractor import PdfTextExtractor
from quant_cn.industry_graph.section_detector import SectionDetector

REPO = Path("/Volumes/Treasury/quant_cn")
PROTO = Path("/Volumes/Treasury/quant_cn_lake/meta/runs/proto")
OUT = Path("/Volumes/Treasury/quant_cn/research_space/prototypes/chain_view/view_data.json")
COMPANIES = {
    "002130.SZ": "沃尔核材", "300308.SZ": "中际旭创", "300750.SZ": "宁德时代", "600276.SH": "恒瑞医药",
    "688126.SH": "沪硅产业", "688234.SH": "天岳先进", "000876.SZ": "新希望", "000895.SZ": "双汇发展",
    "002714.SZ": "牧原股份", "300498.SZ": "温氏股份",
}
# named counterparties found in report prose (prototype; phase 4 extracts these with evidence)
NAMED = {
    "688126.SH": [("台积电", "TSMC", "customer", 15), ("联电", "UMC", "customer", 15), ("意法半导体", "STMicroelectronics", "customer", 15),
                  ("威世", "Vishay", "customer", 15), ("中芯国际", None, "customer", 15), ("华虹宏力", None, "customer", 15)],
    "300750.SZ": [("大众", "Volkswagen", "customer", 21), ("宝马", "BMW", "customer", 21), ("Stellantis", "Stellantis", "customer", 21),
                  ("沃尔沃", "Volvo", "customer", 21)],
    "688234.SH": [("博世", "Bosch", "customer", 20)],
    "002130.SZ": [("福特", "Ford", "customer", 30)],
}


# prototype stand-in for the phase-4 bz_item mapping (D-103): item -> taxonomy ids, "pending" = sector file not written yet
MANUAL = {
    ("002130.SZ", "新能源汽车产品"): ["PROD_AUTO_HV_HARNESS"], ("002130.SZ", "电力产品"): ["PROD_PWR_CABLE_ACCESSORY"],
    ("002130.SZ", "通信线缆"): ["PROD_COMM_HIGH_SPEED_COPPER", "PROD_COMM_DAC"], ("002130.SZ", "风力发电"): ["PROD_UTIL_ONSHORE_WIND"],
    ("300308.SZ", "光通信收发模块"): ["PROD_COMM_DATACOM_MODULE", "PROD_COMM_800G_MODULE"],
    ("300750.SZ", "动力电池系统"): ["PROD_PWR_EV_BATTERY"], ("300750.SZ", "储能电池系统"): ["PROD_PWR_STORAGE_CELL"],
    ("300750.SZ", "电池材料及回收"): ["PROD_PWR_LFP", "PROD_NFM_BATTERY_RECYCLING"], ("300750.SZ", "电池矿产资源"): ["PROD_NFM_SPODUMENE_CONCENTRATE"],
    ("600276.SH", "肿瘤"): ["PROD_PHAR_ONCOLOGY_API", "PROD_PHAR_INNOVATIVE_SMALL_MOLECULE"], ("600276.SH", "神经科学"): ["PROD_PHAR_PSYCHIATRIC_DRUG", "PROD_PHAR_ANESTHETIC"],
    ("600276.SH", "代谢和心血管"): ["PROD_PHAR_CARDIOVASCULAR_DRUG", "PROD_PHAR_GLP1"], ("600276.SH", "免疫和呼吸系统"): ["PROD_PHAR_AUTOIMMUNE_MAB"],
    ("600276.SH", "造影剂"): ["PROD_PHAR_CONTRAST_AGENT"],
    ("688126.SH", "300mm半导体硅片"): ["PROD_ELEC_300MM_WAFER"], ("688126.SH", "200mm及以下尺寸半导体硅片"): ["PROD_ELEC_200MM_WAFER"],
    ("688234.SH", "碳化硅半导体材料"): ["PROD_ELEC_SIC_SUBSTRATE"],
    ("000876.SZ", "饲料"): ["PROD_AGRI_FEED"], ("000876.SZ", "猪产业"): ["MAT_LIVE_HOGS", "PROD_AGRI_PIGLET"],
    ("000895.SZ", "生鲜猪产品"): ["PROD_FOOD_HOG_SLAUGHTER", "PROD_FOOD_FRESH_PORK"], ("000895.SZ", "包装肉制品"): ["PROD_FOOD_HIGH_TEMP_MEAT", "PROD_FOOD_LOW_TEMP_MEAT"],
    ("002714.SZ", "生猪"): ["MAT_LIVE_HOGS", "PROD_AGRI_BREEDING_PIG", "PROD_AGRI_PIGLET"], ("002714.SZ", "屠宰、肉食产品"): ["PROD_FOOD_HOG_SLAUGHTER", "PROD_FOOD_FRESH_PORK"],
    ("002714.SZ", "饲料原料"): ["PROD_AGRI_FEED"],
    ("300498.SZ", "肉猪类"): ["MAT_LIVE_HOGS"], ("300498.SZ", "肉鸡类"): ["PROD_AGRI_YELLOW_BROILER"], ("300498.SZ", "兽药"): ["PROD_AGRI_VET_DRUG"],
    ("300498.SZ", "肉制品加工产品"): ["PROD_FOOD_LOW_TEMP_MEAT"],
}
ADJUST = re.compile(r"抵消|抵减|调整|^合计")
ELIM = re.compile(r"抵消|抵减")
# prototype: which business lines an elimination row sits between (upstream item, downstream item)
INTERNAL = {"002714.SZ": ("生猪", "屠宰、肉食产品"), "000895.SZ": ("生鲜猪产品", "包装肉制品")}


def call_tushare(api, params):
    tok = next(re.match(r'TUSHARE_TOKEN\s*=\s*"?([^"\n]*)', l)[1] for l in open(REPO / ".env") if l.startswith("TUSHARE_TOKEN"))
    body = json.dumps({"api_name": api, "token": tok, "params": params, "fields": ""}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request("http://api.tushare.pro", data=body, headers={"Content-Type": "application/json"}), timeout=60))
    d = r["data"]
    return [dict(zip(d["fields"], it)) for it in d["items"]]


def load_taxonomy():
    nodes, edges, sectors = {}, [], {}
    for f in sorted((REPO / "config/industry_chain").glob("*.yaml")):
        doc = yaml.safe_load(f.read_text()) or {}
        sec = doc.get("sector") or {}
        if sec:
            sectors[str(sec["sw_l1"])] = sec["name"]
        for n in doc.get("nodes", []):
            nodes.setdefault(n["id"], {"id": n["id"], "t": n["type"], "n": n["name"], "en": n.get("name_en"),
                                       "p": n.get("parent"), "s": n.get("segment"), "k": n.get("kind"),
                                       "imp": n.get("import_dependence"), "al": n.get("aliases", []),
                                       "sec": str(sec.get("sw_l1", "")) or None})
        edges += [[e[0], e[1], e[2]] for e in doc.get("edges", []) if isinstance(e, list) and len(e) == 3]
    edges = [e for e in edges if e[0] in nodes and e[2] in nodes]
    return nodes, edges, sectors


def match_product(item, products):
    """Longest taxonomy name/alias contained in the bz_item (or containing it)."""
    best, best_len = None, 0
    clean = re.sub(r"[（(].*?[)）]|及|与|和", "", item)
    for pid, label in products:
        if len(label) >= 2 and (label in clean or (len(clean) >= 3 and clean in label)):
            if len(label) > best_len:
                best, best_len = pid, len(label)
    return best


nodes, edges, sectors = load_taxonomy()
MERGED = yaml.safe_load((REPO / "config/industry_chain/_merged_ids.yaml").read_text()) or {}
MERGED = MERGED.get("merged", MERGED) if isinstance(MERGED, dict) else {}
MANUAL = {k: (v if v == "pending" else [MERGED.get(i, i) for i in v]) for k, v in MANUAL.items()}
products = [(i, str(lbl)) for i, n in nodes.items() if n["t"] == "product" for lbl in [n["n"], *n["al"]]]
parser = AnnualReportParser(PdfTextExtractor(), SectionDetector(), CounterpartyTableParser())
pdfs = {re.search(r"(\d{6})", Path(p).name)[1]: Path(p) for p in glob.glob(str(PROTO / "*.pdf"))}
companies = []
for code, name in COMPANIES.items():
    parsed = parser.parse_report(pdfs[code[:6]])
    sec = {s.key: [s.page_start, s.page_end] for s in parsed.sections}
    cp_page = sec.get("counterparties", [None])[0]
    rows_p = [r for r in call_tushare("fina_mainbz_vip", {"ts_code": code, "period": "20251231", "type": "P"}) if r["bz_sales"]]
    rows_d = [r for r in call_tushare("fina_mainbz_vip", {"ts_code": code, "period": "20251231", "type": "D"}) if r["bz_sales"]]
    total = max((r["bz_sales"] for r in rows_p), default=0) or 1
    skip = re.compile(r"^(产品|合计|其他业务|主营业务|小计)$")
    revenue = []
    elims = [{"item": r["bz_item"], "sales": r["bz_sales"], "pct": round(100 * r["bz_sales"] / total, 2)}
             for r in rows_p if ELIM.search(r["bz_item"])]
    for r in rows_p:
        if skip.match(r["bz_item"]) or ADJUST.search(r["bz_item"]) or r["bz_sales"] >= total * 0.999 and len(rows_p) > 1:
            continue
        manual = MANUAL.get((code, r["bz_item"]))
        rule = match_product(r["bz_item"], products)
        if manual == "pending":
            pids, how = [], "pending"
        elif manual:
            pids, how = [m for m in manual if m in nodes], "manual"
        elif rule:
            pids, how = [rule], "rule"
        else:
            pids, how = [], "none"
        revenue.append({"item": r["bz_item"], "sales": r["bz_sales"], "pct": round(100 * r["bz_sales"] / total, 2),
                        "gm": round(100 * (r["bz_profit"] or 0) / r["bz_sales"], 1) if r["bz_sales"] else None,
                        "pids": pids, "how": how})
    tot_d = max((r["bz_sales"] for r in rows_d), default=0) or 1
    regions = [{"item": r["bz_item"], "pct": round(100 * r["bz_sales"] / tot_d, 2)} for r in rows_d
               if not skip.match(r["bz_item"]) and not ADJUST.search(r["bz_item"]) and r["bz_sales"] < tot_d * 0.999]

    def table(t):
        return {"total_pct": t.total_share_pct, "total": t.total_amount, "consistent": t.is_consistent,
                "rows": [{"rank": x.rank, "name": x.name, "amount": x.amount, "pct": x.share_pct, "anon": x.is_anonymous} for x in t.rows]}
    companies.append({"code": code, "name": name, "pages": parsed.n_pages, "sections": sec, "md_share": round(parsed.chapter_share, 3),
                      "cp_page": cp_page, "revenue": revenue, "regions": regions, "eliminations": elims,
                      "internal": list(INTERNAL.get(code, ())),
                      "customers": table(parsed.customers), "suppliers": table(parsed.suppliers),
                      "named": [{"name": n, "en": en, "role": role, "page": pg} for n, en, role, pg in NAMED.get(code, [])],
                      "source": f"{name} 2025年年度报告"})
    print(code, name, "revenue items", len(revenue), "mapped", sum(1 for x in revenue if x["pids"]))

# inferred counterparties (D-102 amount rule): same amount within 0.5%, chain path, unique
flow = {}
for a, r, b in edges:
    if r == "uses_material":
        a, b = b, a
    if r in ("upstream_of", "component_of", "uses_material", "used_in"):
        flow.setdefault(a, set()).add(b)


def reaches(src, dst, hops=3):
    frontier, seen = set(src), set(src)
    for _ in range(hops):
        frontier = {y for x in frontier for y in flow.get(x, ())} - seen
        if frontier & set(dst):
            return True
        seen |= frontier
    return False


pids = {c["code"]: [p for r in c["revenue"] for p in r["pids"]] for c in companies}
cands = []
for a in companies:
    for cr in a["customers"]["rows"]:
        for b in companies:
            if b is a:
                continue
            for sr in b["suppliers"]["rows"]:
                diff = abs(cr["amount"] - sr["amount"]) / sr["amount"]
                if diff <= 0.005 and reaches(pids[a["code"]], pids[b["code"]]):
                    cands.append((a, cr, b, sr, diff))
for a, cr, b, sr, diff in cands:
    if sum(1 for x in cands if x[1] is cr) == 1 and sum(1 for x in cands if x[3] is sr) == 1:
        cr["inferred"] = {"code": b["code"], "name": b["name"], "diff": round(diff * 100, 3), "their_rank": sr["rank"]}
        sr["inferred"] = {"code": a["code"], "name": a["name"], "diff": round(diff * 100, 3), "their_rank": cr["rank"]}
        print("inferred:", a["name"], "客户", cr["rank"], "→", b["name"], "供应商", sr["rank"], f"{diff:.3%}")

# anonymous-counterparty profiles (D-102): which business line, which downstream stage, region, name hints
import duckdb
RAW = Path("/Volumes/Treasury/quant_cn_lake/raw")
con = duckdb.connect()
concepts = con.sql(f"""SELECT m.con_code, i.name FROM read_parquet('{RAW}/ths_member/*.parquet', union_by_name=true) m
    JOIN read_parquet('{RAW}/ths_index/*.parquet') i USING (ts_code) WHERE i.type IN ('N', 'TH')""").df()
NAME_CONCEPT = re.compile(r"^(特斯拉|华为|比亚迪|中芯国际|英伟达|苹果|小米|长安汽车|宁德时代|蔚来|理想|赛力斯|阿里|腾讯|字节|百度|小鹏|问界|鸿蒙)")
OVERSEAS = re.compile(r"境外|海外|国外|外销")
downstream, rel_of = {}, {}
REL_RANK = {"uses_material": 0, "component_of": 0, "used_in": 1, "upstream_of": 2}
for a, r, b in edges:
    if r == "uses_material":
        a, b = b, a
    if r in REL_RANK:
        downstream.setdefault(a, []).append(b)
        rel_of[(a, b)] = min(REL_RANK[r], rel_of.get((a, b), 9))
for c in companies:
    hints = sorted({n for n in concepts[concepts.con_code == c["code"]]["name"] if NAME_CONCEPT.search(n)})
    overseas = sum(r["pct"] for r in c["regions"] if OVERSEAS.search(r["item"]))
    has_region = bool(c["regions"])
    cum = 0.0
    for row in c["customers"]["rows"]:
        cum += row["pct"]
        if not row["anon"] or row.get("inferred"):
            continue
        lines = [r for r in sorted(c["revenue"], key=lambda r: -r["sales"]) if r["sales"] >= row["amount"] and r["pids"]]
        stages, seen = [], set()
        for line in lines[:2]:
            for p in line["pids"][:2]:
                for d in downstream.get(p, []):
                    n = nodes.get(d)
                    if n and d not in seen and n["t"] in ("product", "end_market", "material"):
                        seen.add(d)
                        stages.append({"id": d, "name": n["n"], "seg": nodes[n["s"]]["n"] if n.get("s") in nodes else None,
                                       "via": line["item"], "rel": rel_of.get((p, d), 9)})
        domestic = 100 - overseas
        if not has_region:
            region = "不确定"
        elif row["pct"] > domestic + 0.01:
            region = "确定境外"      # a customer larger than all domestic revenue must be overseas
        elif row["pct"] > overseas + 0.01:
            region = "确定境内"
        elif overseas >= 80:
            region = "大概率境外"
        elif overseas <= 20:
            region = "大概率境内"
        else:
            region = "不确定"
        degree = lambda x: len(downstream.get(x["id"], [])) + sum(1 for v in downstream.values() if x["id"] in v)
        own_names = "".join(nodes[p]["n"] for line in lines[:2] for p in line["pids"][:2])
        overlap = lambda x: len(set(x["name"]) & set(own_names))
        stages.sort(key=lambda x: (nodes[x["id"]]["t"] == "end_market", x["rel"], -overlap(x), -degree(x)))
        row["profile"] = {"lines": [l["item"] for l in lines[:2]], "stages": stages[:4], "region": region,
                          "overseas_pct": round(overseas, 2), "hints": hints}

# DeepSeek pilot (plan 12 ph4a): business-section reading, quote-checked
APPS = Path("/Volumes/Treasury/quant_cn/research_space/prototypes/chain_view/applications.json")
apps = json.loads(APPS.read_text()) if APPS.exists() else {}
for c in companies:
    a = apps.get(c["code"])
    if not a:
        continue
    c["llm"] = {"lines": a["lines"], "customer_types": a["customer_types"], "counterparties": a["counterparties"]}
    c["named"] = [{"name": p["name"], "en": None, "role": "customer", "page": p["evidence"]["page"], "detail": p["detail"]}
                  for p in a["counterparties"] if p["role"] == "customer"]
    for row in c["customers"]["rows"]:
        prof = row.get("profile")
        if not prof:
            continue
        llm_stages, types = [], []
        for line in prof["lines"]:
            for app in a["lines"].get(line, []):
                if app["weight"] == "主要":
                    llm_stages.append({"id": app["node_id"], "name": app["name"], "quote": app["evidence"]["quote"], "page": app["evidence"]["page"]})
            types += a["customer_types"].get(line, [])
        prof["llm_stages"] = llm_stages[:4]
        prof["customer_types"] = list(dict.fromkeys(types))[:5]

VALS = Path("/Volumes/Treasury/quant_cn/research_space/prototypes/chain_view/valuations.json")
vals = json.loads(VALS.read_text()) if VALS.exists() else {}
for c in companies:
    c["valuations"] = vals.get(c["code"][:6], [])

OUT.write_text(json.dumps({"nodes": list(nodes.values()), "edges": edges, "sectors": sectors, "companies": companies},
                          ensure_ascii=False, separators=(",", ":")))
print("nodes", len(nodes), "edges", len(edges), "bytes", OUT.stat().st_size)
