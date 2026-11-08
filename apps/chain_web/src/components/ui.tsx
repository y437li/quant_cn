import type { ReactNode } from "react";
import { IMP_ZH, TYPE_ZH } from "../lib/format";
import { typeOf } from "../graph/taxonomy";
import { useApp } from "./context";

/** Purpose: small shared UI parts (tags, links, KPI tiles, tabs). */
export function Tag(p: { kind?: "ev" | "risk" | "prior"; title?: string; children: ReactNode; strong?: boolean; dim?: boolean }) {
  return <span className={`tag ${p.kind || ""}`} title={p.title} style={p.strong ? { fontWeight: 700 } : p.dim ? { opacity: 0.55 } : undefined}>{p.children}</span>;
}
export function NodeLink(p: { id: string; plain?: boolean }) {
  const { tx, select } = useApp();
  const n = tx.N[p.id];
  if (!n) return <>{p.id}</>;
  return (
    <>
      <button type="button" className="link" onClick={() => select({ kind: "node", id: p.id })}>{n.n}</button>
      {!p.plain && <> <Tag>{TYPE_ZH[typeOf(n)]}</Tag>{n.imp && n.imp !== "low" && <> <Tag kind="risk">{IMP_ZH[n.imp]}</Tag></>}</>}
    </>
  );
}
export function CompanyLink(p: { code: string; name: string }) {
  const { select } = useApp();
  return <button type="button" className="link" onClick={() => select({ kind: "company", id: p.code })}>{p.name}</button>;
}
export function Kpis(p: { items: [ReactNode, string][] }) {
  return <div className="kpis">{p.items.map(([v, l], i) => <div className="kpi" key={i}><b>{v}</b><span>{l}</span></div>)}</div>;
}
export function Row(p: { left: ReactNode; right?: ReactNode }) {
  return <div className="row"><span>{p.left}</span>{p.right != null && <span>{p.right}</span>}</div>;
}
export function Empty(p: { children: ReactNode }) { return <p className="empty">{p.children}</p>; }
export function Note(p: { children: ReactNode }) { return <p className="note">{p.children}</p>; }
export interface TabDef { key: string; label: string; n?: number }
export function Tabs(p: { tabs: TabDef[]; active: string; onPick: (k: string) => void }) {
  return (
    <nav className="tabs" role="tablist">
      {p.tabs.map((t) => (
        <button key={t.key} type="button" role="tab" aria-selected={t.key === p.active} className={t.key === p.active ? "on" : ""} onClick={() => p.onPick(t.key)} data-tab={t.key}>
          {t.label}{t.n != null && <span className="n">{t.n}</span>}
        </button>
      ))}
    </nav>
  );
}
export function Bar(p: { value: number; kind?: "cust" | "supp"; color?: number }) {
  const bg = p.color != null ? { background: `var(--c${(p.color % 6) + 1})` } : {};
  return <div className={`bar ${p.kind || ""}`}><span style={{ width: `${Math.max(0, Math.min(100, p.value))}%`, ...bg }} /></div>;
}
