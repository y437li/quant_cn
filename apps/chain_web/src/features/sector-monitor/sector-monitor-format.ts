import type { SectorChart, SectorDoc } from "../../api/client";

/** Purpose: one table column of the 行业监控 company table. */
export interface SectorColumn { key: string; label: string; unit: string; pct?: boolean }

const DIGITS: Record<string, number> = { "亿元": 1, "%": 1, "元": 3, "款": 0, "名": 0, "城": 0, "次": 0 };

/**
 * Purpose: a value with the precision of its unit. Contract: null / NaN → "—"; 亿元 and % one decimal, 元 three, 款 名 城 次 none;
 * any other unit two decimals; thousands separated.
 */
export function formatValue(v: number | null | undefined, unit: string): string {
  if (v == null || Number.isNaN(v)) return "—";
  const d = DIGITS[unit] ?? 2;
  return v.toLocaleString("zh-CN", { minimumFractionDigits: d, maximumFractionDigits: d });
}

/** Purpose: a 0..1 percentile as "86%". Contract: null → "—". */
export const formatPct = (v: number | null | undefined): string => (v == null ? "—" : `${Math.round(v * 100)}%`);

/**
 * Purpose: a short period label. Contract: "20261117" → "11-17" (a day), "20260930" with a quarter-end day → "26Q3",
 * "2026-10" → "26年10月", "2025" → "2025"; anything else unchanged.
 */
export function periodLabel(p: string): string {
  if (/^\d{4}-\d{2}$/.test(p)) return `${p.slice(2, 4)}年${Number(p.slice(5))}月`;
  if (/^\d{8}$/.test(p)) {
    const md = p.slice(4);
    const q = { "0331": 1, "0630": 2, "0930": 3, "1231": 4 }[md];
    return q ? `${p.slice(2, 4)}Q${q}` : `${p.slice(4, 6)}-${p.slice(6)}`;
  }
  return p;
}

/** Purpose: the sorted union of every line's periods (the shared x axis). Contract: string order = time order. */
export function listPeriods(chart: SectorChart): string[] {
  return [...new Set(chart.lines.flatMap((l) => l.points.map((p) => p[0])))].sort();
}

/**
 * Purpose: the company-table columns of a sector: per chart that has company values its latest value (unless the chart
 * says in_table: false) and its extra column (YTD yoy, valuation level, recent surveys), then realised vol and its
 * percentile per window, then 散户温度计. Contract: whole-market charts (house prices, approvals) have no row keys and
 * are left out; column keys are the table row keys.
 */
export function listColumns(doc: SectorDoc): SectorColumn[] {
  const rowKeys = new Set(doc.table.flatMap((r) => Object.keys(r)));
  const cols: SectorColumn[] = [];
  for (const c of doc.charts.filter((c) => c.key !== "realized_vol")) {
    if (c.in_table !== false && rowKeys.has(c.key)) cols.push({ key: c.key, label: c.title.replace(/\(.*\)$/, ""), unit: c.unit });
    if (c.extra && rowKeys.has(c.extra.key)) cols.push({ key: c.extra.key, label: c.extra.label, unit: c.extra.unit });
  }
  const vols = [...rowKeys].filter((k) => /^vol_\d+$/.test(k)).sort((a, b) => Number(a.slice(4)) - Number(b.slice(4)));
  for (const v of vols) {
    cols.push({ key: v, label: `${v.slice(4)}日波动`, unit: "%" });
    cols.push({ key: `${v}_pct`, label: "3年分位", unit: "", pct: true });
  }
  cols.push({ key: "retail_gauge", label: "散户温度计", unit: "" });
  return cols;
}

/**
 * Purpose: a rank move since the previous capture. Contract: rank null → ""; prev null → "新"; up (smaller rank) →
 * "↑n", down → "↓n", same → "–".
 */
export function rankChange(rank: number | null, prev: number | null): string {
  if (rank == null) return "";
  if (prev == null) return "新";
  if (rank === prev) return "–";
  return rank < prev ? `↑${prev - rank}` : `↓${rank - prev}`;
}

const MARKETS: Record<string, string> = {
  cn: "中国", us: "美国", jp: "日本", kr: "韩国", tw: "台湾", hk: "香港", sg: "新加坡", th: "泰国", id: "印尼", my: "马来",
  ph: "菲律宾", vn: "越南", in: "印度", gb: "英国", de: "德国", fr: "法国", it: "意大利", es: "西班牙", ca: "加拿大",
  au: "澳洲", br: "巴西", mx: "墨西哥", tr: "土耳其", sa: "沙特", ae: "阿联酋", ru: "俄罗斯",
};

/** Purpose: the Chinese name of an App Store market code. Contract: unknown codes upper-cased; null → "". */
export const marketName = (code: string | null): string => (code == null ? "" : MARKETS[code] ?? code.toUpperCase());
