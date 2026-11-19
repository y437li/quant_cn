/** Pages of the app shell and their URL hashes (plan 15 ph7j). */
export type Page = "chain" | "dupont" | "macro" | "futures" | "volatility" | "rates" | "buyback" | "tasks" | "sector-monitor" | "etf" | "factors" | "holdings" | "watchlist" | "opportunities";

export interface NavItem { page: Page; label: string }
export interface NavGroup { title: string; items: NavItem[] }

/** Purpose: the sidebar: 市场 / 监测 / 我的. Contract: every page except none appears exactly once. */
export const NAV: NavGroup[] = [
  { title: "市场", items: [{ page: "chain", label: "产业链图谱" }, { page: "dupont", label: "杜邦坐标" }] },
  { title: "监测", items: [{ page: "macro", label: "宏观监测" }, { page: "futures", label: "期货监测" }, { page: "volatility", label: "波动率监测" }, { page: "rates", label: "利率汇率" }, { page: "buyback", label: "回购增持" }, { page: "sector-monitor", label: "行业监控" }, { page: "etf", label: "ETF 监测" }, { page: "factors", label: "因子监控" }, { page: "tasks", label: "更新状态" }] },
  { title: "我的", items: [{ page: "holdings", label: "持仓" }, { page: "watchlist", label: "观察账本" }, { page: "opportunities", label: "机会清单" }] },
];

const SIMPLE: Page[] = ["macro", "futures", "volatility", "rates", "buyback", "tasks", "sector-monitor", "etf", "factors", "holdings", "watchlist", "opportunities"];

/**
 * Purpose: the page a URL hash shows. Contract: "#macro" etc. → that page; "#dupont=a,b" → dupont with codes;
 * "#co=" / "#node=" / "#sector=", empty or unknown → chain.
 */
export function readRoute(hash: string): { page: Page; codes: string[] } {
  const h = hash.replace(/^#/, "");
  const d = h.match(/^dupont=?(.*)$/);
  if (d) return { page: "dupont", codes: d[1].split(",").filter(Boolean).map(decodeURIComponent) };
  const p = SIMPLE.find((x) => x === h);
  return { page: p ?? "chain", codes: [] };
}

/** Purpose: the hash of a page (chain has none: its hash is the selection). Contract: inverse of readRoute. */
export function routeHash(page: Page, codes: string[] = []): string {
  if (page === "dupont") return "#dupont=" + codes.map(encodeURIComponent).join(",");
  return page === "chain" ? "" : "#" + page;
}
