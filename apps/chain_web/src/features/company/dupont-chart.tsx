import { useEffect, useState } from "react";
import type { Company } from "../../api/client";
import { DRIVER_ZH, DupontPlane, FLAG_ZH } from "../../components/dupont-plane";
import { Note } from "../../components/ui";
import { useApp } from "../../components/context";

/**
 * Purpose: the company's DuPont path FY2019→latest on the fixed market plane, with play / pause / slider:
 * the company moves step by step and the market cloud switches to the same fiscal year.
 */
type Pt = { p: string; roe: number; at: number; npm: number | null; lev: number | null; driver?: string; flag?: string };
export function DupontChart({ c }: { c: Company }) {
  const { select } = useApp();
  const path = (c as Company & { dupont?: Pt[] }).dupont || [];
  const [step, setStep] = useState(path.length - 1);
  const [playing, setPlaying] = useState(false);
  useEffect(() => { setStep(path.length - 1); setPlaying(false); }, [c.code, path.length]);
  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => setStep((s) => { if (s >= path.length - 1) { setPlaying(false); return s; } return s + 1; }), 900);
    return () => clearInterval(t);
  }, [playing, path.length]);
  if (!path.length) return <Note>没有杜邦数据。</Note>;
  const cur = path[Math.min(step, path.length - 1)];
  const year = cur.p.replace("年化", ""); // "2025" or the latest quarter "2026Q3" (annualised)
  const play = () => { if (step >= path.length - 1) setStep(0); setPlaying(!playing); };
  return (
    <>
      <div className="player">
        <button type="button" className="chip on" onClick={play} aria-label={playing ? "暂停" : "播放"}>{playing ? "❚❚ 暂停" : "▶ 播放"}</button>
        <input type="range" min={0} max={path.length - 1} value={step} onChange={(e) => { setPlaying(false); setStep(+e.target.value); }} aria-label="年份" />
        <b className="num">{cur.p}</b>
        <span className="note">ROE {cur.roe}% · 周转 {cur.at} · 净利率 {cur.npm ?? "—"}% · 权益乘数 {cur.lev ?? "—"}</span>
      </div>
      <DupontPlane onPick={(code) => select({ kind: "company", id: code })} year={year} highlight={(m) => m[4] === c.l3 && m[2] !== c.code} paths={[{ label: c.name, pts: path.slice(0, step + 1) }]}
        caption={`红线 = ${c.name} 2019→${cur.p}；蓝点 = 同一申万三级行业（${c.l3 || "—"}）同一年的位置。`} />
      <table className="fin"><thead><tr><th>年度</th><th className="num">ROE</th><th className="num">净利率</th><th className="num">资产周转</th><th className="num">权益乘数</th><th>驱动 / 提示</th></tr></thead>
        <tbody>{path.map((p, i) => <tr key={p.p} className={i === step ? "strong" : ""} onClick={() => { setPlaying(false); setStep(i); }} style={{ cursor: "pointer" }}><td>{p.p}</td><td className="num">{p.roe}%</td><td className="num">{p.npm ?? "—"}%</td><td className="num">{p.at}</td><td className="num">{p.lev ?? "—"}</td><td className="note">{p.driver ? DRIVER_ZH[p.driver] : ""}{p.flag && <span style={{ color: "var(--c5)" }}> {FLAG_ZH[p.flag]}</span>}</td></tr>)}</tbody></table>
      <Note>ROE = 净利率 × 资产周转率 × 权益乘数。向右：周转驱动；向上而周转不变：利润率或杠杆驱动。季度点已年化，背景沿用当年年报。点击表格行可跳到该年。</Note>
    </>
  );
}
