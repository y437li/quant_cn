import type { SectorEarningsRow, SectorEarningsStatus } from "../../api/client";

/** Purpose: "20260930" → "2026Q3". */
export function seasonLabel(endDate: string | null): string {
  if (!endDate) return "—";
  return `${endDate.slice(0, 4)}Q${Math.floor(Number(endDate.slice(4, 6)) / 3)}`;
}

/** Purpose: a % excess with its sign ("+43.8%", "−0.2%"); null → "—". */
export function signedPct(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  const s = Math.abs(v).toFixed(1);
  return v > 0 ? `+${s}%` : v < 0 ? `−${s}%` : "0.0%";
}

const STATUS: Record<SectorEarningsStatus, string> = { firing: "触发", provisional: "临时", none: "" };

/** Purpose: the Chinese status label (blank for none). */
export function statusLabel(s: SectorEarningsStatus): string {
  return STATUS[s];
}

/**
 * Purpose: rows shown by default: every firing and provisional sector, then the `extra` sectors with the highest
 * pre-disclosure excess among the rest (those closest to firing).
 */
export function pickRows(rows: SectorEarningsRow[], extra: number): SectorEarningsRow[] {
  const shown = rows.filter((r) => r.status !== "none");
  const rest = rows.filter((r) => r.status === "none" && r.pre !== null).sort((a, b) => (b.pre ?? 0) - (a.pre ?? 0));
  return [...shown, ...rest.slice(0, extra)];
}
