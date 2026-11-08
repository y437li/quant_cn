import { useState } from "react";
import type { Company, CompanyBrief } from "../../api/client";
import { Tabs } from "../../components/ui";
import { BusinessTab } from "./tab-business";
import { ValuationTab } from "./tab-valuation";
import { CustomersTab, EvidenceTab, OverviewTab, ProductsTab, SuppliersTab } from "./tabs-basic";
import { ChainTab, PeersTab, QuarterlyTab } from "./tabs-more";

/** Purpose: header and tabs of one company (same tabs as the prototype). */
export function CompanyDossier({ c, related }: { c: Company; related: Record<string, CompanyBrief> }) {
  const [tab, setTab] = useState("overview");
  const tabs = [
    { key: "overview", label: "概览" }, { key: "products", label: "产品与服务", n: c.revenue.length },
    { key: "customers", label: "客户", n: (c.customers?.rows.length || 0) + (c.named?.length || 0) }, { key: "suppliers", label: "供应商", n: c.suppliers?.rows.length || 0 },
    { key: "peers", label: "同行", n: (c.peers || []).length }, { key: "chain", label: "上下游" },
    { key: "valuation", label: "估值与指标", n: (c.valuations || []).length }, { key: "quarterly", label: "季报要点", n: (c.quarterly || []).length },
    { key: "business", label: "商业模式" }, { key: "evidence", label: "证据" },
  ];
  const p = { c, related };
  const body: Record<string, JSX.Element> = {
    overview: <OverviewTab {...p} />, products: <ProductsTab {...p} />, customers: <CustomersTab {...p} />, suppliers: <SuppliersTab {...p} />,
    peers: <PeersTab {...p} />, chain: <ChainTab {...p} />, valuation: <ValuationTab c={c} />, quarterly: <QuarterlyTab {...p} />,
    business: <BusinessTab c={c} />, evidence: <EvidenceTab {...p} />,
  };
  const ch = c.sections?.chapter;
  return (
    <>
      <div className="head">
        <div className="eyebrow">公司 · {c.code}</div>
        <h2>{c.name}</h2>
        <div className="meta"><span>来源：{c.source || "—"}</span>{c.pages ? <span>{c.pages} 页</span> : null}{ch && <span>管理层讨论与分析 第 {ch[0]}–{ch[1]} 页</span>}</div>
      </div>
      <Tabs tabs={tabs} active={tab} onPick={setTab} />
      <div className="body" data-testid="tab-body">{body[tab]}</div>
    </>
  );
}
