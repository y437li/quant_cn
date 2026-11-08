"""Plan 12 phase 4a pilot: DeepSeek reads the business sections of the 10 prototype reports.
Writes applications.json next to this file (results after the quote check) and prints usage."""
import glob
import json
import re
from pathlib import Path

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.deep_seek_client import DeepSeekClient
from quant_cn.industry_graph.application_extractor import ApplicationExtractor
from quant_cn.industry_graph.pdf_text_extractor import PdfTextExtractor
from quant_cn.industry_graph.section_detector import SectionDetector

HERE = Path(__file__).parent
PROTO = Path("/Volumes/Treasury/quant_cn_lake/meta/runs/proto")
CACHE = Path("/Volumes/Treasury/quant_cn_lake/meta/llm_cache")
KEEP = ("business", "industry", "competitiveness")

data = json.loads((HERE / "view_data.json").read_text())
nodes = {n["id"]: n for n in data["nodes"]}
down = {}
for a, r, b in data["edges"]:
    if r == "uses_material":
        a, b = b, a
    if r in ("upstream_of", "component_of", "uses_material", "used_in"):
        down.setdefault(a, set()).add(b)
markets = [(i, n["n"]) for i, n in nodes.items() if n["t"] == "end_market"]

config = Config.load()
llm = DeepSeekClient(config.llm, Clock(), CACHE)
extractor = ApplicationExtractor(llm)
reader, detector = PdfTextExtractor(), SectionDetector()
pdfs = {re.search(r"(\d{6})", Path(p).name)[1]: Path(p) for p in glob.glob(str(PROTO / "*.pdf"))}
out = {}
for c in data["companies"]:
    report = reader.read_pages(pdfs[c["code"][:6]])
    sections = {s.key: s for s in detector.list_sections(report)}
    pages = []
    for key in KEEP:
        s = sections.get(key)
        if s:
            pages += [(p, report.pages[p - 1]) for p in range(s.page_start, s.page_end + 1) if (p, report.pages[p - 1]) not in pages]
    pages.sort()
    seeds = {p for r in c["revenue"] for p in r["pids"]}
    frontier, cand = set(seeds), set()
    for _ in range(2):
        frontier = {y for x in frontier for y in down.get(x, ())} - cand - seeds
        cand |= frontier
    candidates = sorted({(i, nodes[i]["n"]) for i in cand if i in nodes} | set(markets))
    lines = [r["item"] for r in c["revenue"]]
    result = extractor.fetch_applications(c["name"], pages, lines, candidates)
    out[c["code"]] = {
        "pages": [p for p, _ in pages][:1] + [p for p, _ in pages][-1:],
        "lines": result.lines, "customer_types": result.customer_types,
        "counterparties": [{**cp, "evidence": vars(cp["evidence"])} for cp in result.counterparties],
        "dropped": result.dropped, "tokens": result.tokens, "cached": result.cached,
    }
    for line, apps in result.lines.items():
        for a in apps:
            a["evidence"] = vars(a["evidence"])
    out[c["code"]]["lines"] = result.lines
    print(c["name"], "pages", len(pages), "| apps", sum(len(v) for v in result.lines.values()),
          "| parties", len(result.counterparties), "| dropped", result.dropped, "| tokens", result.tokens, "| cached", result.cached)

(HERE / "applications.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
line = llm.record_usage(Path("/Volumes/Treasury/quant_cn_lake/meta/llm_usage.jsonl"), "plan12-4a applications pilot")
print(f"DeepSeek: {line['calls']} calls ({line['cached']} from cache), {line['prompt_tokens']:,} in / "
      f"{line['completion_tokens']:,} out tokens, cost ¥{line['cost_cny']:.4f}")
