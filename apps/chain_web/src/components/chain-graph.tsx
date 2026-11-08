import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";
import { useEffect, useRef } from "react";
import type { El } from "../graph/elements";
import { buildStyles } from "../graph/styles";

cytoscape.use(dagre);
const LANE_ROWS = 12;

/**
 * Purpose: draw elements with the layout of the view: preset swim lanes (company), cose (network) or dagre LR.
 * Contract: props.elements replace the graph; onPick(id) on node tap; exposes zoom / fit / resize via props.control.
 */
export interface GraphControl { zoomBy: (f: number) => void; fit: () => void; resize: () => void }
export function ChainGraph(props: { elements: El[]; layout: "lanes" | "cose" | "dagre"; onPick: (id: string) => void; control: React.MutableRefObject<GraphControl | null> }) {
  const box = useRef<HTMLDivElement>(null);
  const cy = useRef<cytoscape.Core | null>(null);
  const pick = useRef(props.onPick);
  pick.current = props.onPick;

  useEffect(() => {
    const c = cytoscape({ container: box.current, wheelSensitivity: 0.25, minZoom: 0.1, maxZoom: 4, style: buildStyles() });
    c.on("tap", "node", (e) => pick.current(e.target.id()));
    cy.current = c;
    props.control.current = {
      zoomBy: (f) => c.zoom({ level: c.zoom() * f, renderedPosition: { x: c.width() / 2, y: c.height() / 2 } }),
      fit: () => c.fit(undefined, 30),
      resize: () => { c.resize(); c.fit(undefined, 30); },
    };
    const media = matchMedia("(prefers-color-scheme: dark)");
    const restyle = () => c.style(buildStyles());
    media.addEventListener("change", restyle);
    return () => { media.removeEventListener("change", restyle); c.destroy(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const c = cy.current;
    if (!c) return;
    c.elements().remove();
    c.add(props.elements as cytoscape.ElementDefinition[]);
    if (props.layout === "lanes") {
      const cols: Record<string, cytoscape.NodeSingular[]> = {};
      c.nodes().forEach((n) => { (cols[n.data("col")] ||= []).push(n); });
      const colW = Math.max(170, c.width() / 4.2);
      Object.entries(cols).forEach(([col, list]) => {
        list.sort((a, b) => b.data("rank") - a.data("rank"));
        // a long lane wraps into sub-columns of LANE_ROWS so the graph is not squeezed
        const rows = list.filter((n) => n.data("type") !== "lane");
        const sub = Math.max(1, Math.ceil(rows.length / LANE_ROWS));
        const x0 = (+col - 1) * colW * 1.6;
        rows.forEach((n, i) => { n.position({ x: x0 + Math.floor(i / LANE_ROWS) * 150, y: (i % LANE_ROWS) * 58 }); });
        list.filter((n) => n.data("type") === "lane").forEach((n) => n.position({ x: x0 + ((sub - 1) * 150) / 2, y: -50 }));
      });
      c.layout({ name: "preset", fit: false } as cytoscape.LayoutOptions).run();
    } else if (props.layout === "cose") {
      c.layout({ name: "cose", animate: false, nodeRepulsion: () => 9000, idealEdgeLength: () => 90, numIter: 1500 } as cytoscape.LayoutOptions).run();
    } else {
      c.layout({ name: "dagre", rankDir: "LR", nodeSep: 14, rankSep: 70, edgeSep: 8, animate: false } as cytoscape.LayoutOptions).run();
    }
    c.fit(undefined, 30);
  }, [props.elements, props.layout]);

  return <div ref={box} className="cy" data-testid="graph" />;
}
