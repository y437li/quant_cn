import type { FactorMonitor, MonitoredFactor } from "../../api/client";
import { ymd } from "../watchlist/watchlist-format";

/**
 * Purpose: pure display helpers of the 因子监控 page (plan 15 phase 7c, D-132). Returns and volatility are
 * computed in Python (FactorMonitorBuilder); this only formats, sorts and picks them.
 * Contract: fractions in, strings out; null / undefined → "—".
 */

/** Display names of the risk-model styles; unknown factors fall back to their label. */
export const STYLE_ZH: Record<string, string> = {
  country: "市场", size: "市值", beta: "贝塔", momentum: "动量", residual_volatility: "残差波动",
  non_linear_size: "非线性市值", book_to_price: "账面市值比", liquidity: "流动性", earnings_yield: "盈利收益率",
  growth: "成长", leverage: "杠杆", us_sensitivity: "美股敏感度", cash_flow_yield: "现金流收益率",
  usd_sensitivity: "美元敏感度", ai_dc_sensitivity: "AIDC 敏感度", arm_sensitivity: "Arm 敏感度",
  gold_sensitivity: "黄金敏感度", us_rate_sensitivity: "美债利率敏感度", oil_sensitivity: "原油敏感度",
  dividend_yield: "股息率",
};

/** Purpose: the shown name of a factor. Contract: styles via STYLE_ZH, industries by their Shenwan label. */
export const factorName = (f: Pick<MonitoredFactor, "factor" | "label" | "kind">): string =>
  f.kind === "industry" ? f.label : STYLE_ZH[f.factor] ?? f.label;

/** Purpose: a signed percent. Contract: 0.0123 → "+1.23%"; −0.004 → "−0.40%"; null → "—". */
export const signedPct = (v: number | null | undefined, digits = 2): string => {
  if (v == null) return "—";
  const s = (Math.abs(v) * 100).toFixed(digits);
  return (Number(s) === 0 ? "" : v > 0 ? "+" : "−") + s + "%";
};

/** Purpose: an annualised volatility. Contract: 0.182 → "18.2%"; null → "—". */
export const volPct = (v: number | null | undefined): string => (v == null ? "—" : (v * 100).toFixed(1) + "%");

/** Purpose: a sigma move. Contract: −1.234 → "−1.2σ"; 0.04 → "0.0σ"; null → "—". */
export const sigma = (v: number | null | undefined): string => {
  if (v == null) return "—";
  const s = Math.abs(v).toFixed(1);
  return (Number(s) === 0 ? "" : v > 0 ? "+" : "−") + s + "σ";
};

/** Purpose: colour class of a return or move. Contract: > 0 → "up", < 0 → "down", 0 / null → "flat". */
export const moveClass = (v: number | null | undefined): "up" | "down" | "flat" =>
  v == null || v === 0 ? "flat" : v > 0 ? "up" : "down";

/** Purpose: flag an unusual day or regime. Contract: |sigma_move| ≥ 2 or vol_ratio ≥ 1.5 → true. */
export const isAlert = (f: Pick<MonitoredFactor, "sigma_move" | "vol_ratio">): boolean =>
  Math.abs(f.sigma_move ?? 0) >= 2 || (f.vol_ratio ?? 0) >= 1.5;

/** Purpose: split factors into the style table (country first) and the industry table. Contract: order kept. */
export function splitFactors(factors: MonitoredFactor[]): { styles: MonitoredFactor[]; industries: MonitoredFactor[] } {
  return { styles: factors.filter((f) => f.kind !== "industry"), industries: factors.filter((f) => f.kind === "industry") };
}

/** Purpose: paired (date, value) points of one series, nulls dropped. Contract: dates and values aligned by index. */
export const toPoints = (dates: string[], values: (number | null)[]): { d: string; v: number }[] =>
  dates.flatMap((d, i) => (values[i] == null ? [] : [{ d, v: values[i] as number }]));

/**
 * Purpose: the one-sentence headline of the page.
 * Contract: no factors → ""; otherwise the as-of date, the market (country) return today, and the largest style move in σ.
 */
export function monitorHeadline(doc: FactorMonitor): string {
  if (!doc.factors.length) return "";
  const country = doc.factors.find((f) => f.kind === "country");
  const styles = doc.factors.filter((f) => f.kind === "style" && f.sigma_move != null);
  const top = styles.sort((a, b) => Math.abs(b.sigma_move ?? 0) - Math.abs(a.sigma_move ?? 0))[0];
  return `${ymd(doc.as_of)} 收盘：市场因子 ${signedPct(country?.ret.d1)}` +
    (top ? `；风格里动得最多的是 ${factorName(top)} ${signedPct(top.ret.d1)}（${sigma(top.sigma_move)}）` : "") + "。";
}
