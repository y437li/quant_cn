"""Plan 13 pilot: ValuationExtractor over 3 broker reports × 10 companies; writes valuations.json; logs cost."""
import json
from pathlib import Path

import duckdb

from quant_cn.core.clock import Clock
from quant_cn.core.config import Config
from quant_cn.data_loading.deep_seek_client import DeepSeekClient
from quant_cn.industry_graph.pdf_text_extractor import PdfTextExtractor
from quant_cn.industry_graph.valuation_extractor import ValuationExtractor

HERE = Path(__file__).parent
REPORTS = Path("/Volumes/Treasury/quant_cn_lake/meta/runs/proto/reports")
LAKE = Path("/Volumes/Treasury/quant_cn_lake")

basic = duckdb.sql(f"SELECT name, ts_code FROM '{LAKE}/curated/reference/stock_basic.parquet'").fetchall()
name_to_code = {n: c for n, c in basic}
config = Config.load()
llm = DeepSeekClient(config.llm, Clock(), LAKE / "meta" / "llm_cache")
extractor = ValuationExtractor(llm)
reader = PdfTextExtractor()
picked = json.loads((REPORTS / "picked.json").read_text())
out = {}
for code, reports in picked.items():
    out[code] = []
    for rep in reports:
        pages = extractor.list_pages(reader.read_pages(Path(rep["file"])).pages)
        r = extractor.fetch_valuation(f"{rep['org']} {rep['date']}《{rep['title']}》", pages, name_to_code)
        v = {"rating": r.rating, "target_price": r.target_price, "methods": r.methods, "forecasts": r.forecasts,
             "comparables": r.comparables, "assumptions": r.assumptions, "logic": r.logic}
        out[code].append({**{k: rep[k] for k in ("info_code", "title", "org", "date", "pages")},
                          "valuation": v, "dropped": r.dropped, "tokens": r.tokens})
        print(code, rep["org"], rep["date"], "|", [(m.get("method"), m.get("multiple"), m.get("multiple_kind"), m.get("base_year")) for m in r.methods][:3],
              "| TP", (r.target_price or {}).get("value"), "| comps", sum(1 for c in r.comparables if c["ts_code"]), "/", len(r.comparables), "| dropped", r.dropped)
(HERE / "valuations.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
line = llm.record_usage(LAKE / "meta" / "llm_usage.jsonl", "plan13 ph2 ValuationExtractor pilot rerun")
print(f"DeepSeek: {line['calls']} calls ({line['cached']} cached), {line['prompt_tokens']:,} in / {line['completion_tokens']:,} out, cost ¥{line['cost_cny']:.4f}")
