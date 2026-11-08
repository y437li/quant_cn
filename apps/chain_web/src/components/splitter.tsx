import { useEffect, useRef } from "react";

/** Purpose: drag to resize the dossier (280 px .. viewport − 320 px); double-click resets; width kept in localStorage. */
const KEY = "chainWebDossierWidth";
export function Splitter({ onResize }: { onResize: () => void }) {
  const drag = useRef(false);
  const set = (w: number) => {
    const main = document.querySelector("main") as HTMLElement;
    main.style.setProperty("--dw", Math.round(Math.max(280, Math.min(w, main.clientWidth - 320))) + "px");
  };
  useEffect(() => { try { const w = Number(localStorage.getItem(KEY)); if (w) set(w); } catch { /* storage blocked */ } }, []);
  return (
    <div className="splitter" role="separator" aria-orientation="vertical" title="拖动调整宽度，双击恢复"
      onPointerDown={(e) => { drag.current = true; e.currentTarget.setPointerCapture(e.pointerId); e.currentTarget.classList.add("drag"); }}
      onPointerMove={(e) => { if (drag.current) set((document.querySelector("main") as HTMLElement).getBoundingClientRect().right - e.clientX); }}
      onPointerUp={(e) => {
        drag.current = false; e.currentTarget.classList.remove("drag");
        try { localStorage.setItem(KEY, String(parseInt(getComputedStyle(document.querySelector("main") as HTMLElement).getPropertyValue("--dw")))); } catch { /* storage blocked */ }
        onResize();
      }}
      onDoubleClick={() => { set(440); try { localStorage.removeItem(KEY); } catch { /* storage blocked */ } onResize(); }} />
  );
}
