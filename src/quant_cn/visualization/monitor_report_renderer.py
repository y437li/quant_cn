"""The 持仓监测 morning e-mail (plan 15 ph7e, D-136)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
from typing import Any

from quant_cn.core.mail_sender import MailContent
from quant_cn.visualization.email_format import AMBER, DOWN, MUTED, EmailFormat
from quant_cn.visualization.email_html import EmailHtml
from quant_cn.visualization.report_section import ReportSection

STYLE = {
    "country": "市场",
    "size": "市值",
    "beta": "贝塔",
    "momentum": "动量",
    "residual_volatility": "残差波动",
    "non_linear_size": "非线性市值",
    "book_to_price": "账面市值比",
    "liquidity": "流动性",
    "earnings_yield": "盈利收益率",
    "growth": "成长",
    "leverage": "杠杆",
    "us_sensitivity": "美股敏感度",
    "cash_flow_yield": "现金流收益率",
    "usd_sensitivity": "美元敏感度",
    "dividend_yield": "股息率",
}
RETAIL_INFLOW = 0.8  # RetailGauge percentile at which a holding is flagged (plan 21 ph5)
SIGMA_ALERT, VOL_RATIO_ALERT = 2.0, 1.5


class MonitorReportRenderer:
    """
    Purpose:
        Render the 持仓监测 e-mail from the app's JSON documents: alerts first (holdings with
        the D-155 散户过热 avoid flag, stronger wording for avoid_strong (D-167), listed before
        everything else; position flags, holdings whose RetailGauge reads retail inflow,
        position conditions met, factor moves of 2σ or vol ratio 1.5), then holdings tiles,
        positions by share of risk, style exposures, per-stock exposures, factor performance,
        national-team ETF flows and industries; the 宏观 block (ph7h) adds a summary line and,
        on new prints, its table. A missing document
        turns its sections into a "数据缺失" note.

    Contract:
        Input:
            sections: Sequence[ReportSection]  -- optional blocks (宏观, 期货), in order
        Output:
            instance; `render(docs, today) -> MailContent`
        Raises:
            (none at construction)

    Used by:
        visualization.MorningReportBuilder  -- first e-mail
        cli.ReportCommands                  -- injected type or call

    Test cases:
        TC-MRR-001  every section renders from fixtures; alerts list flags, inflow and conditions
        TC-MRR-002  a missing document gives its 数据缺失 sections; the others still render
        TC-MRR-003  with sections: summary lines and the 宏观 table on a new print
        TC-MRR-004  a position with cost <= 0 (diluted cost, D-166) shows 已回本 as its 盈亏
        TC-MRR-005  avoid / avoid_strong holdings are the first alerts, in plain words
    """

    def __init__(self, sections: Sequence[ReportSection] = ()) -> None:
        self._sections = list(sections)

    def render(self, docs: Mapping[str, dict[str, Any] | None], today: str) -> MailContent:
        """
        Purpose:
            The e-mail for `today` from holdings_risk, factor_monitor and etf_proxy documents.

        Contract:
            Input:
                docs:  {"holdings_risk", "factor_monitor", "etf_proxy", section DOCs} -> doc/None
                today: str  -- YYYYMMDD of the report
            Output:
                MailContent  -- subject "持仓监测 <date> · N 条提醒", HTML, plain text
            Raises:
                (none)
        """
        h, f, e = docs.get("holdings_risk"), docs.get("factor_monitor"), docs.get("etf_proxy")
        alerts = self._list_alerts(h, f)
        lines = [s.build_summary(docs.get(s.DOC)) for s in self._sections]
        summary = (alerts or ["今天没有提醒。"]) + [x for x in lines if x]
        rows = self._build_holdings(h) + self._build_factors(f, h) + self._build_etf(e)
        rows += "".join(s.build_rows(docs.get(s.DOC)) for s in self._sections)
        as_of = (h or f or {}).get("as_of", "")
        model = (f or h or {}).get("model", "—")
        sub = f"数据截至 {EmailFormat.format_ymd(as_of)} 收盘 · 风险模型 {model}"
        html = EmailHtml.build_page(
            "持仓监测", EmailFormat.format_day(today), sub, [escape(s) for s in summary], rows
        )
        subject = f"持仓监测 {EmailFormat.format_ymd(today)} · {len(alerts)} 条提醒"
        text = "\n".join([subject, sub, *("· " + s for s in summary), "完整内容请用 HTML 查看。"])
        return MailContent(subject, html, text)

    def _list_alerts(self, h: dict[str, Any] | None, f: dict[str, Any] | None) -> list[str]:
        out: list[str] = []
        hot: list[str] = []
        if h:
            names = {p["code"]: p["name"] for p in h.get("positions", [])}
            for code, r in h.get("reviews", {}).items():
                name = names.get(code, code)
                out += [f"{name}：{flag['message']}" for flag in r.get("flags") or []]
                chips = r.get("chips") or {}
                gauge = chips.get("retail_gauge")
                if chips.get("gauge_avoid_strong") == 1.0:
                    hot.append(f"{name}：散户过热，温度计 {gauge:.2f}，连续 3 次 ≥ 0.9，强烈回避")
                elif chips.get("gauge_avoid") == 1.0:
                    hot.append(f"{name}：散户过热，温度计 {gauge:.2f}（≥ 0.9），注意回避")
                elif gauge is not None and gauge >= RETAIL_INFLOW:
                    out.append(f"{name}：散户温度计 {gauge:.2f}，散户在进")
                met = [c["label"] for c in r.get("conditions") or [] if c["state"] == "met"]
                if met:
                    period = (
                        EmailFormat.format_ymd(r.get("period")) if r.get("period") else "最新数据"
                    )
                    out.append(
                        f"{name}：条件已满足 {len(met)} 条（{'；'.join(met)}；按 {period} 财报）"
                    )
        for x in (f or {}).get("factors", []):
            sigma, ratio = x.get("sigma_move"), x.get("vol_ratio")
            label = STYLE.get(x["factor"], x["label"])
            if abs(sigma or 0) >= SIGMA_ALERT:
                out.append(f"因子异动：{label} 昨日 {EmailFormat.format_sigma(sigma)}")
            elif (ratio or 0) >= VOL_RATIO_ALERT:
                out.append(f"因子波动放大：{label} 实际 / 预测波动 {ratio:.1f} 倍")
        return hot + out

    def _build_holdings(self, h: dict[str, Any] | None) -> str:
        if not h or not h.get("as_of"):
            return EmailHtml.build_missing("持仓", "holdings_risk.json")
        return EmailHtml.build_section(
            "持仓", "合并为一个组合", self._build_tiles(h)
        ) + EmailHtml.build_pair(
            EmailHtml.build_section("持仓明细", "按风险贡献排序", self._build_positions(h)),
            EmailHtml.build_section(
                "风格敞口", f"相对 {h['benchmark']}，单位：标准差", self._build_styles(h)
            ),
        )

    @staticmethod
    def _build_tiles(h: dict[str, Any]) -> str:
        r, base = h["risk"], h["stock_value"] - h["pnl"]
        pnl_pct = EmailFormat.format_pct(h["pnl"] / base if base else None, 1)
        factor, specific = (
            EmailFormat.format_vol(r.get("factor")),
            EmailFormat.format_vol(r.get("specific")),
        )
        mix = f"因子 {factor} · 个股 {specific}"
        tiles = [
            EmailHtml.build_tile(
                "总资产",
                EmailFormat.format_yuan(h["value"]),
                f"现金 {EmailFormat.format_yuan(h['cash'])}",
            ),
            EmailHtml.build_tile(
                "浮动盈亏",
                EmailFormat.format_yuan(h["pnl"]),
                pnl_pct,
                EmailFormat.get_color(h["pnl"]),
            ),
            EmailHtml.build_tile("组合波动", EmailFormat.format_vol(r.get("total")), mix),
            EmailHtml.build_tile(
                "跟踪误差", EmailFormat.format_vol(r.get("active_total")), f"相对 {h['benchmark']}"
            ),
        ]
        return (
            '<table role="presentation" cellpadding="0" cellspacing="6" style="width:100%"><tr>'
            + "".join(tiles)
            + "</tr></table>"
        )

    @staticmethod
    def _build_positions(h: dict[str, Any]) -> str:
        ranked = sorted(
            (p for p in h["positions"] if p["contrib"] is not None), key=lambda p: -p["contrib"]
        )
        head = [
            EmailHtml.build_th("股票", "left"),
            EmailHtml.build_th("仓位"),
            EmailHtml.build_th("盈亏"),
            EmailHtml.build_th("风险贡献"),
        ]
        rows = [
            [
                EmailHtml.build_td(p["name"], "left", mono=False),
                EmailHtml.build_td(EmailFormat.format_vol(p["weight"])),
                EmailHtml.build_td(
                    "已回本"
                    if (p.get("cost") is not None and p["cost"] <= 0)
                    else EmailFormat.format_pct(p["pnl_pct"], 1),
                    color=EmailFormat.get_color(p.get("pnl", p["pnl_pct"])),
                ),
                EmailHtml.build_td(EmailFormat.format_vol(p["contrib"]), bold=True),
            ]
            for p in ranked
        ]
        return EmailHtml.build_table(head, rows)

    @staticmethod
    def _build_styles(h: dict[str, Any]) -> str:
        styles = sorted(
            (x for x in h["factors"] if x["kind"] == "style"), key=lambda x: -abs(x["active"] or 0)
        )
        head = [
            EmailHtml.build_th("风格", "left"),
            EmailHtml.build_th("相对基准"),
            EmailHtml.build_th("−2 · 0 · +2", "center"),
        ]
        rows = [
            [
                EmailHtml.build_td(STYLE.get(x["factor"], x["label"]), "left", mono=False),
                EmailHtml.build_td(f"{x['active']:+.2f}" if x["active"] is not None else "—"),
                EmailHtml.build_bar(x["active"]),
            ]
            for x in styles[:11]
        ]
        return EmailHtml.build_table(head, rows)

    def _build_factors(self, f: dict[str, Any] | None, h: dict[str, Any] | None) -> str:
        if not f or not f.get("factors"):
            return EmailHtml.build_missing("因子表现", "factor_monitor.json")
        sub = "底色 = 昨日 ≥2σ 或 实际 / 预测波动 ≥1.5"
        return EmailHtml.build_section(
            "因子表现", sub, self._build_factor_table(f)
        ) + EmailHtml.build_section("行业因子", "申万一级，昨日", self._build_industry_table(f))

    @staticmethod
    def _build_factor_table(f: dict[str, Any]) -> str:
        wins = [("d1", "昨日"), ("w1", "1周"), ("m1", "1月"), ("ytd", "今年")]
        rows = []
        for x in (x for x in f["factors"] if x["kind"] in ("country", "style")):
            sigma, ratio = x.get("sigma_move"), x.get("vol_ratio")
            hot = abs(sigma or 0) >= SIGMA_ALERT or (ratio or 0) >= VOL_RATIO_ALERT
            name = STYLE.get(x["factor"], x["label"])
            row = [EmailHtml.build_td(name, "left", mono=False, bg="#fff4e5" if hot else None)]
            row += [
                EmailHtml.build_td(
                    EmailFormat.format_pct(x["ret"][k]), color=EmailFormat.get_color(x["ret"][k])
                )
                for k, _ in wins
            ]
            row += [
                EmailHtml.build_td(
                    EmailFormat.format_sigma(sigma), color=EmailFormat.get_color(sigma)
                ),
                EmailHtml.build_td(EmailFormat.format_vol(x.get("forecast_vol"))),
            ]
            rows.append(row)
        head = [EmailHtml.build_th("因子", "left"), *(EmailHtml.build_th(n) for _, n in wins)]
        return EmailHtml.build_table(
            [*head, EmailHtml.build_th("昨日σ"), EmailHtml.build_th("预测波动")], rows
        )

    @staticmethod
    def _build_industry_table(f: dict[str, Any]) -> str:
        inds = sorted(
            (x for x in f["factors"] if x["kind"] == "industry"),
            key=lambda x: -(x["ret"]["d1"] or 0),
        )

        def cells(x: dict[str, Any]) -> list[str]:
            d1 = x["ret"]["d1"]
            return [
                EmailHtml.build_td(x["label"], "left", mono=False),
                EmailHtml.build_td(EmailFormat.format_pct(d1), color=EmailFormat.get_color(d1)),
            ]

        rows = [cells(a) + cells(b) for a, b in zip(inds[:5], inds[::-1][:5], strict=False)]
        head = [
            EmailHtml.build_th("涨幅前五", "left"),
            EmailHtml.build_th("昨日"),
            EmailHtml.build_th("跌幅前五", "left"),
            EmailHtml.build_th("昨日"),
        ]
        return EmailHtml.build_table(head, rows)

    def _build_etf(self, e: dict[str, Any] | None) -> str:
        if not e or not e.get("recent"):
            return EmailHtml.build_missing("国家队 ETF", "etf_proxy.json")
        core = (e.get("totals") or {}).get("core") or {}
        recent = e["recent"][-5:]
        rows = [
            [
                EmailHtml.build_td(EmailFormat.format_ymd(r["date"]), "left"),
                EmailHtml.build_td(
                    self._format_yi(r.get("core")),
                    color=AMBER if (r.get("core") or 0) < 0 else DOWN,
                ),
                EmailHtml.build_td(self._format_yi(r.get("other")), color=MUTED),
            ]
            for r in recent
        ]
        table = EmailHtml.build_table(
            [
                EmailHtml.build_th("日期", "left"),
                EmailHtml.build_th("核心 ETF 净流入"),
                EmailHtml.build_th("其他"),
            ],
            rows,
        )
        position, ytd = self._format_yi(core.get("position")), self._format_yi(core.get("flow_ytd"))
        sub = f"核心持仓 {position} · 今年净流入 {ytd}"
        return EmailHtml.build_section("国家队 ETF", sub, table)

    @staticmethod
    def _format_yi(v: float | None) -> str:
        return "—" if v is None else ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):,.0f} 亿"
