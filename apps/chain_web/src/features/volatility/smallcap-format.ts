import type { SmallCapEpisode, SmallCapPoint, SmallCapRow, SmallCapSharePoint, SmallCapState, VolPoint } from "../../api/client";

export const STATE_LABEL: Record<SmallCapState, string> = { on: "已触发", near: "接近", off: "未到", info: "参考" };

/** Purpose: rows for the table: triggered first, the rest in document order. Contract: no row is lost or repeated. */
export function orderRows(rows: SmallCapRow[]): SmallCapRow[] {
  return [...rows.filter((r) => r.state === "on"), ...rows.filter((r) => r.state !== "on")];
}

const num = (v: number, digits = 0) => v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });

/** Purpose: a row's latest value by unit: 只 count, 占比 percent, 点 index level, % vol, 亿 signed flow, 涨跌 signed day return (ph5). Contract: null → "—". */
export function formatScValue(r: Pick<SmallCapRow, "value" | "unit">): string {
  const v = r.value;
  if (v == null) return "—";
  if (r.unit === "占比") return `${Math.round(v * 100)}%`;
  if (r.unit === "点") return num(v);
  if (r.unit === "%") return `${v.toFixed(1)}%`;
  if (r.unit === "亿") return `${v < 0 ? "−" : "+"}${num(Math.abs(v), 1)}亿`;
  if (r.unit === "涨跌") return `${v < 0 ? "−" : "+"}${Math.abs(v * 100).toFixed(1)}%`;
  return `${num(v)}${r.unit}`;
}

/** Purpose: a row's trigger: % (vol) rows are percentile triggers "≥ 90% 分位", levels "≤ 6,075", shares "≥ 70%", counts "≥ 500只". Contract: none → "". */
export function formatScTrigger(r: Pick<SmallCapRow, "trigger" | "unit">): string {
  const t = r.trigger;
  if (t == null) return "";
  if (r.unit === "%") return `≥ ${Math.round(t * 100)}% 分位`;
  if (r.unit === "点") return `≤ ${num(t)}`;
  if (r.unit === "占比") return `≥ ${Math.round(t * 100)}%`;
  if (r.unit === "涨跌") return `≤ −${Math.round(Math.abs(t) * 100)}%`;
  return `≥ ${num(t)}${r.unit}`;
}

/** Purpose: the 中证1000 closes of the history as chart points. Contract: sessions without a close are dropped. */
export const smallPoints = (h: SmallCapPoint[]): VolPoint[] =>
  h.filter((p) => p.small != null).map((p) => ({ date: p.date, value: p.small as number }));

/** Purpose: the financing balance (亿) of the history as chart points (plan 30 ph4). Contract: sessions without it are dropped. */
export const marginPoints = (h: SmallCapPoint[]): VolPoint[] =>
  h.filter((p) => p.rz != null).map((p) => ({ date: p.date, value: p.rz as number }));

/** Purpose: the balance as % of float market cap, as chart points. Contract: fraction × 100; sessions without it are dropped. */
export const marginSharePoints = (h: SmallCapPoint[]): VolPoint[] =>
  h.filter((p) => p.rz_circ != null).map((p) => ({ date: p.date, value: (p.rz_circ as number) * 100 }));

/** Range of 融资余额 / 流通市值 (%) on the six 中证1000 bottom days since 2019 (research 20261119_margin_share). */
export const SHARE_BOTTOM_REFS = [1.94, 2.54];

/** Purpose: the share chart points (plan 30 ph6): the weekly series since 2019 when present, else the 1-year daily line. Contract: values in %. */
export const marginShareChartPoints = (w: { history: SmallCapPoint[]; margin_share_long?: SmallCapSharePoint[] }): VolPoint[] =>
  w.margin_share_long && w.margin_share_long.length > 1 ? w.margin_share_long.map((p) => ({ date: p.date, value: p.share })) : marginSharePoints(w.history);

type LongWatch = { history: SmallCapPoint[]; margin_share_long?: SmallCapSharePoint[]; margin_episodes?: SmallCapEpisode[] };
const longRz = (w: LongWatch): VolPoint[] =>
  (w.margin_share_long ?? []).filter((p) => p.rz != null).map((p) => ({ date: p.date, value: p.rz as number }));

/** Purpose: the balance chart points (plan 30 ph7): weekly 亿 since 2019 when the long series carries rz, else the 1-year daily line. Contract: values in 亿. */
export const marginChartPoints = (w: LongWatch): VolPoint[] => {
  const long = longRz(w);
  return long.length > 1 ? long : marginPoints(w.history);
};

/** Purpose: dashed lines on the balance chart: the long high × (1 + each past episode depth) (ph7). Contract: [] without the long series or episodes; ascending. */
export const marginDepthRefs = (w: LongWatch): number[] => {
  const long = longRz(w);
  if (long.length < 2) return [];
  const high = Math.max(...long.map((p) => p.value));
  return (w.margin_episodes ?? []).map((e) => high * (1 + e.depth)).sort((a, b) => a - b);
};

/** Purpose: the watch levels (点 rows' triggers) drawn on the 中证1000 chart. Contract: ascending, no nulls. */
export const levelRefs = (rows: SmallCapRow[]): number[] =>
  rows.filter((r) => r.unit === "点" && r.trigger != null).map((r) => r.trigger as number).sort((a, b) => a - b);

/** Purpose: the panel headline. Contract: triggered names (new ones marked), then near ones; "没有触发" when none fired. */
export function smallCapHeadline(rows: SmallCapRow[], fresh: string[]): string {
  const on = rows.filter((r) => r.state === "on").map((r) => r.name + (fresh.includes(r.key) ? "（新）" : ""));
  const near = rows.filter((r) => r.state === "near").map((r) => `${r.name} ${formatScValue(r)}`);
  return (on.length ? `已触发 ${on.join("、")}` : "没有触发") + (near.length ? `；接近：${near.join("、")}` : "") + "。";
}
