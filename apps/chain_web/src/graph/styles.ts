import type cytoscape from "cytoscape";

/** Purpose: Cytoscape stylesheet from the page's CSS variables (light and dark). */
export function buildStyles(): cytoscape.StylesheetStyle[] {
  const v = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const body = v("--body");
  // padding is a valid Cytoscape style the bundled typings omit
  const sheet = [
    { selector: "node", style: { label: "data(label)", "font-family": body, "font-size": 11, color: v("--ink"), "text-valign": "center", "text-halign": "center", "text-wrap": "wrap", "text-max-width": "96px", width: "label", height: "label", padding: "8px", shape: "round-rectangle", "background-color": v("--product-fill"), "border-width": 1.5, "border-color": v("--c1") } },
    { selector: "node[type='service']", style: { "border-style": "dashed", "background-color": v("--product-fill"), "border-color": v("--c6") } },
    { selector: "node[type='company']", style: { "background-color": v("--company"), color: v("--panel"), "border-width": 0, "font-weight": 700, "font-size": 12, padding: "10px" } },
    { selector: "node[type='material']", style: { shape: "cut-rectangle", "background-color": v("--material-fill"), "border-color": v("--c3"), "border-width": 2, color: v("--ink") } },
    { selector: "node[type='technology']", style: { shape: "round-octagon", "background-color": v("--tech-fill"), "border-color": v("--c4"), "border-width": 2, color: v("--ink") } },
    { selector: "node[type='end_market']", style: { shape: "barrel", "background-color": v("--market"), "border-width": 0, color: v("--panel"), "font-weight": 700 } },
    { selector: "node[type='segment']", style: { shape: "round-tag", "border-color": v("--segment"), "border-width": 1.5, "background-color": v("--segment-fill") } },
    { selector: "node[type='counterparty']", style: { shape: "ellipse", "background-color": v("--cp-fill"), "border-color": v("--cp"), "border-width": 1.5, color: v("--ink"), "font-size": 10, padding: "6px" } },
    { selector: "node[type='foreign']", style: { shape: "ellipse", "background-color": v("--cp-fill"), "border-color": v("--c5"), "border-width": 2, color: v("--ink") } },
    { selector: "node[imp='high']", style: { "border-color": v("--risk"), "border-width": 2.5 } },
    { selector: "node[focus=1]", style: { "border-width": 3, "border-color": v("--evidence") } },
    { selector: "node[type='lane']", style: { shape: "rectangle", "background-opacity": 0, "border-width": 0, color: v("--muted"), "font-size": 11, "font-weight": 700, events: "no" } },
    { selector: "edge", style: { width: 1.2, "curve-style": "bezier", "target-arrow-shape": "triangle", "arrow-scale": 0.8, "line-color": v("--prior"), "target-arrow-color": v("--prior"), "line-style": "dashed", label: "data(label)", "font-size": 9, color: v("--muted"), "text-background-color": v("--panel"), "text-background-opacity": 0.9, "text-background-padding": "2px" } },
    { selector: "edge[kind='produces']", style: { "line-style": "solid", width: 2.4, "line-color": v("--evidence"), "target-arrow-color": v("--evidence"), color: v("--evidence") } },
    { selector: "edge[kind='sells']", style: { "line-style": "solid", width: 2, "line-color": v("--customer"), "target-arrow-color": v("--customer"), color: v("--customer") } },
    { selector: "edge[kind='buys']", style: { "line-style": "solid", width: 2, "line-color": v("--supplier"), "target-arrow-color": v("--supplier"), color: v("--supplier") } },
    { selector: "edge[kind='named']", style: { "line-style": "dotted", width: 2, "line-color": v("--customer"), "target-arrow-color": v("--customer") } },
    { selector: "edge[kind='app']", style: { "line-style": "solid", width: 1.8, "line-color": v("--market"), "target-arrow-color": v("--market"), color: v("--market") } },
    { selector: "edge[kind='peer']", style: { "line-style": "solid", width: 1, "line-color": v("--line"), "target-arrow-color": v("--line") } },
  ];
  return sheet as unknown as cytoscape.StylesheetStyle[];
}
