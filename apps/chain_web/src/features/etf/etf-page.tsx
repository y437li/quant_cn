import { EtfProxyPanel } from "../watchlist/etf-proxy-panel";
import { EtfStylePanel } from "./etf-style-panel";

/**
 * Purpose: the ETF 监测 page at #etf (plan 15 ph7b / 7g / 7j): 风格 ETF 资金强度 (银行, 红利) and the 国家队 ETF panel (positions and flows of the broad-index
 * ETFs the national team holds vs the rest), moved out of 观察账本 into its own sidebar entry.
 * Contract: read-only; the panel loads GET /api/etf-proxy itself and shows its own empty / error note.
 */
export function EtfPage() {
  return (
    <div className="wl-page" data-page="etf">
      <div className="wl-head">
        <h2>ETF 监测</h2>
        <p>银行、红利 ETF 的资金是否过热；宽基 ETF 的份额和资金流（国家队重仓的核心 ETF 与其他 ETF 分开统计，仓位按今日价格计）。每个工作日自动更新。</p>
      </div>
      <EtfStylePanel />
      <EtfProxyPanel />
    </div>
  );
}
