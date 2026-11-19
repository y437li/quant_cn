import type { ProxyStyle } from "../../api/client";

export const STATUS_ZH: Record<ProxyStyle["status"], string> = { hot: "过热", cooled: "降温", normal: "正常" };

/** Purpose: the one-line reading of a style. Contract: names the status, z and the 20-day flow vs AUM; "—" parts when missing. */
export function styleHeadline(s: ProxyStyle): string {
  const z = s.z == null ? "—" : (s.z > 0 ? "+" : s.z < 0 ? "−" : "") + Math.abs(s.z).toFixed(1);
  const pct = s.flow_pct == null ? "—" : (s.flow_pct > 0 ? "+" : s.flow_pct < 0 ? "−" : "") + Math.abs(s.flow_pct * 100).toFixed(1) + "%";
  const flow = s.flow_window == null ? "—" : `${s.flow_window > 0 ? "+" : ""}${s.flow_window.toFixed(0)} 亿`;
  return `${STATUS_ZH[s.status]} · z ${z} · 20 日净流入 ${flow}（占规模 ${pct}）`;
}

/** Purpose: the z history as chart points. Contract: points without a z are dropped. */
export const stylePoints = (s: ProxyStyle): { x: string; v: number }[] =>
  s.history.filter((h) => h.z != null).map((h) => ({ x: h.d, v: h.z as number }));
