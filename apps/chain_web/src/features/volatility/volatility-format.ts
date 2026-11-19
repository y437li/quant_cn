import type { VolLine } from "../../api/client";

export const GROUPS = ["美国", "A股"] as const;

/** Purpose: lines by group in GROUPS order. Contract: groups without lines are left out; order inside a group kept. */
export function groupLines(lines: VolLine[]): [string, VolLine[]][] {
  const known: string[] = [...GROUPS];
  const names = [...known, ...lines.map((s) => s.group).filter((g) => !known.includes(g))];
  return [...new Set(names)].map((g) => [g, lines.filter((s) => s.group === g)] as [string, VolLine[]]).filter(([, rows]) => rows.length > 0);
}

/** Purpose: one decimal, "—" for null; signed adds "+" and a minus sign. */
export function formatVol(v: number | null, signed = false): string {
  if (v == null) return "—";
  const sign = v < 0 ? "−" : signed && v > 0 ? "+" : "";
  return sign + Math.abs(v).toFixed(1);
}

/** Purpose: "20261113" → "2026-11-13". Contract: empty → "—". */
export const dayLabel = (d: string): string => (d ? `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}` : "—");

/** Purpose: the chart's reference line: the alert level when set, else the window median. */
export const refLevel = (s: Pick<VolLine, "alerts" | "median">): number => s.alerts.level ?? s.median;

/** Purpose: a line's alert rules as text. Contract: "" when none is set. */
export function alertText(s: Pick<VolLine, "alerts">): string {
  const a = s.alerts, parts: string[] = [];
  if (a.level != null) parts.push(`≥ ${a.level}`);
  if (a.jump != null) parts.push(`单日涨 ≥ ${Math.round(a.jump * 100)}%`);
  if (a.pct != null) parts.push(`≥ 1年 ${Math.round(a.pct * 100)}% 分位`);
  return parts.join("，");
}

/** Purpose: the page headline. Contract: each line's value and percentile, then the alert count. */
export function volHeadline(lines: VolLine[], flags: { message: string }[]): string {
  const parts = lines.map((s) => `${s.name} ${formatVol(s.value)}${s.pct == null ? "" : `（${Math.round(s.pct * 100)}%）`}`);
  return parts.join("，") + (flags.length ? `。提醒：${flags.map((f) => f.message).join("；")}。` : "。没有提醒。");
}
