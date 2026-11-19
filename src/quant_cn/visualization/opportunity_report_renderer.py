"""The 机会清单 morning e-mail (plan 15 ph7e, plan 21 ph5, D-136)."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any

from quant_cn.core.mail_sender import MailContent
from quant_cn.visualization.email_format import DOWN, MUTED, RED, EmailFormat
from quant_cn.visualization.email_html import EmailHtml

MARK = {"met": "✓", "unmet": "✗", "unknown": "?"}
STATUS = {"buy": "可以买", "near": "价到，条件未齐", "wait": "等待"}
ORDER = {"buy": 0, "near": 1, "wait": 2}
RULE = {
    "retail_leaving": "散户离场",
    "inflow": "大单流入",
    "earnings": "利润拐点",
    "valuation": "估值低于5年中位",
    "fit": "不加重持仓风格",
}


class OpportunityReportRenderer:
    """
    Purpose:
        Render the 机会清单 e-mail: the daily opportunity list of plan 21 (new names first, then
        names that stayed, then near-misses with the missing condition, from
        `opportunities.json` written by OpportunityDocument) and the watchlist with its
        condition status (buy / near / wait) and one mark per condition.

    Contract:
        Input:
            (none)
        Output:
            instance; `render(docs, today) -> MailContent`
        Raises:
            (none at construction)

    Used by:
        visualization.MorningReportBuilder  -- second e-mail
        cli.ReportCommands                  -- injected type or call

    Test cases:
        TC-ORR-001  watchlist rows sorted buy, near, wait with condition marks and counts
        TC-ORR-002  opportunities: document order kept (new, stayed, near), near-misses show
                    what is missing, dropped names in the subtitle; absent file -> 数据缺失
    """

    def render(self, docs: Mapping[str, dict[str, Any] | None], today: str) -> MailContent:
        """
        Purpose:
            The e-mail for `today` from the opportunities and watchlist documents.

        Contract:
            Input:
                docs:  {"opportunities", "watchlist"} -> document or None
                today: str  -- YYYYMMDD
            Output:
                MailContent  -- subject "机会清单 <date> · …", HTML, plain text
            Raises:
                (none)
        """
        opp, wl = docs.get("opportunities"), docs.get("watchlist")
        entries = sorted(
            (wl or {}).get("entries", []),
            key=lambda e: ORDER.get(e.get("condition_status", "wait"), 2),
        )
        ready = [e["name"] for e in entries if e.get("condition_status") == "buy"]
        priced = [e["name"] for e in entries if e.get("condition_status") == "near"]
        picks = (opp or {}).get("rows", [])
        listed = [p for p in picks if p.get("status") == "listed"]
        new = [p["name"] for p in listed if p.get("is_new")]
        summary = [
            f"今日机会清单 {len(listed)} 只"
            + (f"（新入选：{'、'.join(new)}）" if new else "")
            + f"，差一条的 {len(picks) - len(listed)} 只"
            if opp
            else "今天没有机会清单文件（opportunities.json），先看观察账本。",
            f"观察账本：可以买 {len(ready)} 只"
            + (f"（{'、'.join(ready)}）" if ready else "")
            + f"；价到但条件未齐 {len(priced)} 只"
            + (f"（{'、'.join(priced)}）" if priced else ""),
        ]
        rows = self._build_opportunities(opp) + self._build_watchlist(wl, entries)
        sub = f"价格截至 {EmailFormat.format_ymd((wl or opp or {}).get('as_of', ''))} 收盘"
        html = EmailHtml.build_page(
            "机会清单", EmailFormat.format_day(today), sub, [escape(s) for s in summary], rows
        )
        subject = (
            f"机会清单 {EmailFormat.format_ymd(today)} · 可以买 {len(ready)} · 价到 {len(priced)}"
        )
        text = "\n".join([subject, sub, *("· " + s for s in summary), "完整内容请用 HTML 查看。"])
        return MailContent(subject, html, text)

    def _build_opportunities(self, opp: dict[str, Any] | None) -> str:
        if opp is None:
            return EmailHtml.build_missing("机会清单", "opportunities.json")
        rows = [self._build_pick(p) for p in opp.get("rows", [])]
        if not rows:
            note = f'<div style="color:{MUTED};font-size:13px">今天没有股票满足全部条件。</div>'
            return EmailHtml.build_section(
                "机会清单", "散户离场 + 大单流入 + 利润拐点 + 估值", note
            )
        head = [
            EmailHtml.build_th("股票", "left"),
            EmailHtml.build_th("温度计"),
            EmailHtml.build_th("利润同比"),
            EmailHtml.build_th("PB / 5年中位"),
            EmailHtml.build_th("大单周数"),
            EmailHtml.build_th("状态", "left"),
        ]
        dropped = "、".join(d["name"] or d["code"] for d in opp.get("dropped", []))
        sub = "新入选在前，再是留在清单上的，最后是差一条的（列出缺什么）" + (
            f"；今天移出：{dropped}" if dropped else ""
        )
        return EmailHtml.build_section("机会清单", sub, EmailHtml.build_table(head, rows))

    @staticmethod
    def _build_pick(p: dict[str, Any]) -> list[str]:
        near = p.get("status") != "listed"
        missing = "、".join(RULE.get(m, m) for m in p.get("missing") or [])
        yoy, pb, med = p.get("np_yoy"), p.get("val_value"), p.get("val_median")
        return [
            EmailHtml.build_td(("🆕 " if p.get("is_new") else "") + p["name"], "left", mono=False),
            EmailHtml.build_td(f"{p['pct']:.2f}" if p.get("pct") is not None else "—"),
            EmailHtml.build_td(f"{yoy * 100:+.0f}%" if yoy is not None else "—"),
            EmailHtml.build_td(f"{pb:.2f} / {med:.2f}" if pb and med else "—"),
            EmailHtml.build_td(
                f"{p['lg_weeks_pos_4w']:.0f}/4" if p.get("lg_weeks_pos_4w") is not None else "—"
            ),
            EmailHtml.build_td(
                "缺：" + missing if near else "全部满足",
                "left",
                mono=False,
                color=MUTED if near else DOWN,
            ),
        ]

    def _build_watchlist(self, wl: dict[str, Any] | None, entries: list[dict[str, Any]]) -> str:
        if wl is None:
            return EmailHtml.build_missing("观察账本", "watchlist.json")
        rows = []
        for e in entries:
            conds = e.get("conditions") or []
            marks = "；".join(f"{MARK[c['state']]} {c['label']}" for c in conds) or "只看价格"
            met = sum(c["state"] == "met" for c in conds)
            need = e.get("conditions_needed") or len(conds)
            band = (
                f"{e['buy_low']:.2f}–{e['buy_high']:.2f}"
                if e["buy_low"] != e["buy_high"]
                else f"{e['buy_high']:.2f}"
            )
            gap = "已到" if e["gap_to_buy"] >= 0 else f"还差 {-e['gap_to_buy'] * 100:.1f}%"
            status = e.get("condition_status", "wait")
            rows.append(
                [
                    EmailHtml.build_td(e["name"], "left", mono=False),
                    EmailHtml.build_td(f"{e['price']:.2f}"),
                    EmailHtml.build_td(band),
                    EmailHtml.build_td(gap, color=DOWN if e["gap_to_buy"] >= 0 else MUTED),
                    EmailHtml.build_td(
                        STATUS[status],
                        "left",
                        mono=False,
                        color=RED if status == "buy" else MUTED,
                        bold=status != "wait",
                    ),
                    EmailHtml.build_td(f"{met}/{need}" if conds else "—"),
                    EmailHtml.build_td(marks, "left", mono=False),
                ]
            )
        head = [
            EmailHtml.build_th("股票", "left"),
            EmailHtml.build_th("现价"),
            EmailHtml.build_th("买入区间"),
            EmailHtml.build_th("距离"),
            EmailHtml.build_th("状态", "left"),
            EmailHtml.build_th("条件"),
            EmailHtml.build_th("逐条（✓ 满足 ✗ 未满足 ? 无数据）", "left"),
        ]
        return EmailHtml.build_section(
            "观察账本", "价格到区间且条件够数才算可以买", EmailHtml.build_table(head, rows)
        )
