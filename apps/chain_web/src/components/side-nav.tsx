import { useState } from "react";
import { NAV, type Page } from "./app-route";

/**
 * Purpose: the left sidebar (plan 15 ph7j): app title, groups 市场 / 监测 / 我的, the current page highlighted, the
 * watchlist badge; below 760 px it folds into a menu button.
 * Contract: open(page) is called on a click; badges maps a page to a count shown when > 0.
 */
export function SideNav({ page, open, badges, subtitle }: { page: Page; open: (p: Page) => void; badges: Partial<Record<Page, number>>; subtitle: string }) {
  const [shown, setShown] = useState(false);
  return (
    <aside className={`side-nav ${shown ? "shown" : ""}`} aria-label="导航">
      <div className="sn-brand">
        <span className="sn-title">A股研究台</span>
        <small>{subtitle}</small>
        <button type="button" className="sn-menu" aria-expanded={shown} onClick={() => setShown(!shown)}>{shown ? "收起" : "菜单"}</button>
      </div>
      <nav>
        {NAV.map((g) => (
          <div className="sn-group" key={g.title}>
            <div className="sn-group-title">{g.title}</div>
            {g.items.map((it) => (
              <button type="button" key={it.page} data-page={it.page} className={`sn-item ${page === it.page ? "on" : ""}`} aria-current={page === it.page ? "page" : undefined}
                onClick={() => { setShown(false); open(it.page); }}>
                <span>{it.label}</span>
                {(badges[it.page] ?? 0) > 0 && <span className="badge" title="接近或已到买入区间的股票数">{badges[it.page]}</span>}
              </button>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}
