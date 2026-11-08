import { useEffect, useRef, useState } from "react";
import { api, type SearchHit } from "../../api/client";
import { useApp } from "../../components/context";

/** Purpose: server-side search for companies and taxonomy nodes; arrow keys and Enter pick. */
export function SearchBox() {
  const { select } = useApp();
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [cur, setCur] = useState(0);
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const s = q.trim();
    if (!s) { setHits([]); return; }
    const t = setTimeout(() => api.findHits(s).then((h) => { setHits(h); setCur(0); setOpen(true); }).catch(() => setHits([])), 150);
    return () => clearTimeout(t);
  }, [q]);
  useEffect(() => {
    const close = (e: MouseEvent) => { if (!box.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, []);
  const pick = (h?: SearchHit) => { if (!h) return; setOpen(false); setQ(""); select({ kind: h.kind, id: h.id }); };
  return (
    <div className="search" ref={box}>
      <input type="search" aria-label="搜索" placeholder="搜索公司、产品、材料、终端市场…" value={q} onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); setCur((c) => (c + (e.key === "ArrowDown" ? 1 : -1) + hits.length) % Math.max(1, hits.length)); }
          if (e.key === "Enter") pick(hits[cur]);
          if (e.key === "Escape") setOpen(false);
        }} />
      {open && q.trim() && (
        <div className="results" role="listbox">
          {hits.length ? hits.map((h, i) => (
            <button type="button" key={h.kind + h.id} className={i === cur ? "on" : ""} onClick={() => pick(h)}><span>{h.label}</span><span className="kind">{h.sub}</span></button>
          )) : <div className="empty">没有匹配项</div>}
        </div>
      )}
    </div>
  );
}
