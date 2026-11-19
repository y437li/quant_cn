"""Plain-language phone alerts from the app's monitor documents (plan 22, D-153)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

DOCS = ("volatility_monitor", "watchlist", "futures_monitor", "macro_monitor")
TRIGGER_OF_DOC = {"volatility_monitor": "volatility", "watchlist": "watchlist",
                  "futures_monitor": "futures", "macro_monitor": "macro"}  # fmt: skip
PLAIN_VOL = {
    "us_vix": "美国股市的「恐慌指数」",
    "cn_50": "A股大盘蓝筹的「恐慌指数」",
    "cn_300": "A股沪深300的「恐慌指数」",
    "cn_500": "A股中盘股的「恐慌指数」",
    "cn_1000": "A股小盘股的「恐慌指数」",
    "cn_star50": "科创板的「恐慌指数」",
}
MACRO_KEYS = ("cpi", "ppi", "pmi_mfg")  # the macro prints worth a message
PLAIN_MACRO = {
    "cpi": "物价（比去年）",
    "ppi": "工厂出厂价格（比去年）",
    "pmi_mfg": "制造业景气指数",
}
# an unmet watchlist condition in plain words, by its metric (the label is used otherwise)
PLAIN_COND = {
    "sm_weeks_neg_4w": "散户还没离开",
    "retail_gauge": "散户还没离开",
    "holders_chg_q": "股东人数还没减少",
    "lg_weeks_pos_4w": "大户资金还没连续买入",
    "lg_net_4w": "大户资金买得还不够多",
    "winner_rate": "赚钱的人还太多（还没跌透）",
    "close": "股价跌破了止损位",
    "bank_etf_z": "银行股还偏热",
}
FUTURES_NAMED = 3  # families named in the futures line; more are counted
FEW_WEEKS, MONTH_SESSIONS = 15, 21  # half-life wording: 两三周内 up to 15 sessions, else months
VOL_HIGH = 1.15  # sample set: 15% above the median reads 偏高 (below median / 1.15: 偏低)
SAMPLE_NOTE = "（这是自动提醒的样例，用的是今天的真实数据。以后只有出现新情况，晚上才会发。）"
CPI_CALM = 1.5  # CPI yoy below this (and >= 0) reads as 还算平稳
PPI_PRESSURE = 3.0  # PPI yoy at or above this reads as 原材料涨价压力大
PMI_LINE = 50.0  # PMI expansion / contraction line
MONTH_LEN = 6  # YYYYMM


@dataclass(frozen=True)
class CardShot:
    """
    Purpose:
        Where an alert's picture is in the app: page hash and CSS selector of the card, and a
        file stem for the screenshot.

    Contract:
        Input:
            page: str (e.g. "#volatility"); selector: str; stem: str (file-name safe);
            title: str -- plain-language card title shown in the picture ("" keeps the app's)
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        visualization.Alert                -- field `shot`
        visualization.AlertMessageBuilder  -- `Alert.shot`
        cli.ReportCommands                 -- pictures for the new alerts
        visualization.CardScreenshotter    -- one screenshot each

    Test cases:
        TC-AMB-001  (via AlertMessageBuilder) a volatility alert carries its card
    """

    page: str
    selector: str
    stem: str
    title: str = ""


@dataclass(frozen=True)
class Alert:
    """
    Purpose:
        One alert line: stable key (sent once per episode), trigger, plain text, optional card.

    Contract:
        Input:
            key: str; trigger: str (core.message_sender.TRIGGERS); text: str;
            shot: CardShot | None
        Output:
            frozen dataclass
        Raises:
            (none)

    Used by:
        visualization.AlertMessageBuilder  -- built by `list_alerts`
        cli.ReportCommands                 -- `notify` command

    Test cases:
        TC-AMB-001  (via AlertMessageBuilder) lines per trigger
    """

    key: str
    trigger: str
    text: str
    shot: CardShot | None = None


class AlertMessageBuilder:
    """
    Purpose:
        Turn the app documents into plain-language alert lines for a phone (no jargon, no
        English abbreviations, each number against its normal level, D-153):
        volatility flags of lines in `volatility_groups` (one line per index, the first rule),
        watchlist names whose price is in the buy range (status "in") or whose buy conditions
        are met (condition_status "buy"), always with the user's buy conditions spelled out
        (met k of n, the unmet ones in plain words via PLAIN_COND, and whether to act; the key
        carries k so a newly met condition alerts again), new futures signals (one line naming
        the families) and new macro prints of MACRO_KEYS. Only triggers in `triggers` are read.
        `build_message` puts the new alerts into one message headed by the day.

    Contract:
        Input:
            triggers:          Sequence[str]  -- triggers switched on (NotifySettings.triggers)
            volatility_groups: Sequence[str]  -- volatility line groups that may alert (A股)
        Output:
            instance; `list_alerts(docs) -> list[Alert]`, `build_message(alerts, day, limit) -> str`
        Raises:
            (none at construction)

    Used by:
        cli.ReportCommands  -- `notify` command

    Test cases:
        TC-AMB-001  lines per trigger: volatility (with its card), watchlist in range and
                    conditions met, futures names, macro print; keys stable
        TC-AMB-005  full: volatility status line without flags (A股 only, 偏高 / 正常 / 偏低),
                    every futures signal, every MACRO_KEYS print even when not new
        TC-AMB-004  watchlist wording: in range without conditions; in range with conditions
                    unmet (count, plain reasons, wait); in range and ready; ready but price
                    above the range; far and not ready gives nothing
        TC-AMB-006  a new reversion flag gives its own plain line (高 / 低, months to normal),
                    kept out of the generic futures line
        TC-AMB-002  triggers switched off and missing documents give no lines; futures with
                    no new flags gives no line; volatility lines outside volatility_groups
                    (美国) give no line
        TC-AMB-003  build_message: day header, one bullet per alert, overflow note past the limit
    """

    def __init__(self, triggers: Sequence[str], volatility_groups: Sequence[str]) -> None:
        self._triggers = set(triggers)
        self._vol_groups = set(volatility_groups)

    def list_alerts(
        self, docs: Mapping[str, dict[str, Any] | None], full: bool = False
    ) -> list[Alert]:
        """
        Purpose:
            Every alert active in the documents, in DOCS order. `full` (the sample set shown
            to a new recipient) also states today's situation where nothing alerts: one line
            on the volatility lines in `volatility_groups`, every current futures signal, and
            the latest print of each MACRO_KEYS series.

        Contract:
            Input:
                docs: Mapping[str, dict | None]  -- DOCS name -> parsed JSON or None
                full: bool                       -- sample set, not only new alerts
            Output:
                list[Alert]  -- keys unique
            Raises:
                (none)
        """
        builders = {
            "volatility_monitor": self._list_volatility,  # bound: reads self._vol_groups
            "watchlist": self._list_watchlist,
            "futures_monitor": self._list_futures,
            "macro_monitor": self._list_macro,
        }
        out: list[Alert] = []
        for name in DOCS:
            doc = docs.get(name)
            if doc and TRIGGER_OF_DOC[name] in self._triggers:
                out += builders[name](doc, full)
        return list({a.key: a for a in out}.values())

    @staticmethod
    def build_message(alerts: Sequence[Alert], day: str, limit: int, sample: bool = False) -> str:
        """
        Purpose:
            One phone message: header with the day, one bullet per alert up to `limit`.

        Contract:
            Input:
                alerts: Sequence[Alert] (non-empty); day: str YYYYMMDD; limit: int > 0;
                sample: bool -- the sample set: SAMPLE_NOTE after the header
            Output:
                str  -- "【今日提醒 M月D日】" then "· <text>" lines; "还有 N 条，详见 App。" when
                        more than limit
            Raises:
                (none)
        """
        head = f"【今日提醒 {int(day[4:6])}月{int(day[6:8])}日】"
        lines = ([SAMPLE_NOTE] if sample else []) + [f"· {a.text}" for a in alerts[:limit]]
        if len(alerts) > limit:
            lines.append(f"还有 {len(alerts) - limit} 条，详见 App。")
        return "\n".join([head, *lines])

    def _list_volatility(self, doc: dict[str, Any], full: bool) -> list[Alert]:
        cls = type(self)
        lines = {x["key"]: x for x in doc.get("lines") or [] if x.get("group") in self._vol_groups}
        out, seen = [], set()
        for flag in doc.get("flags") or []:
            key, kind = flag["key"].split(":")[0], flag["kind"]
            line = lines.get(key)
            if line is None or key in seen:
                continue
            seen.add(key)
            name, v, normal = PLAIN_VOL.get(key, line["name"]), line["value"], line["median"]
            if kind == "jump":
                text = (
                    f"{name}一天涨了 {line['chg_pct'] * 100:.0f}%，到 {v:.0f}，市场突然紧张起来。"
                )
            else:
                text = f"{name}升到 {v:.0f}，平时在 {normal:.0f} 左右，市场比较紧张。"
            shot = CardShot("#volatility", f".mc-card[data-series={key}]", f"vol_{key}",
                            cls._format_vol_title(key, line["name"]))  # fmt: skip
            out.append(Alert(f"vol:{flag['key']}", "volatility", text, shot))
        if full and not out and lines:
            out.append(self._build_vol_status(list(lines.values())))
        return out

    @staticmethod
    def _format_vol_title(key: str, name: str) -> str:
        """Picture title: 「科创板恐慌指数」 from 「科创板的「恐慌指数」」."""
        return PLAIN_VOL.get(key, name).replace("的「恐慌指数」", "恐慌指数")

    @staticmethod
    def _build_vol_status(lines: list[dict[str, Any]]) -> Alert:
        """Today's level of each volatility line against its median (sample set only)."""
        parts = []
        for x in lines:
            v, normal = x["value"], x["median"]
            feel = "偏高" if v > normal * VOL_HIGH else "偏低" if v < normal / VOL_HIGH else "正常"
            short = PLAIN_VOL.get(x["key"], x["name"]).replace("的「恐慌指数」", "")
            parts.append(f"{short.removeprefix('A股')} {v:.0f}（平时 {normal:.0f}，{feel}）")
        top = max(lines, key=lambda x: x["value"] / x["median"])
        shot = CardShot("#volatility", f".mc-card[data-series={top['key']}]", f"vol_{top['key']}",
                        AlertMessageBuilder._format_vol_title(top["key"], top["name"]))  # fmt: skip
        text = "A股「恐慌指数」现在：" + "，".join(parts) + "。"
        return Alert("vol:status", "volatility", text, shot)

    @classmethod
    def _list_watchlist(cls, doc: dict[str, Any], full: bool) -> list[Alert]:
        out = []
        del full  # watchlist alerts are the same in the sample set
        for e in doc.get("entries") or []:
            text, tag = cls._build_watch_text(e)
            if text:
                shot = CardShot("#watchlist", f".wl-card[data-code='{e['code']}']",
                                f"wl_{e['code'].replace('.', '_')}")  # fmt: skip
                out.append(Alert(f"wl:{e['code']}:{tag}", "watchlist", text, shot))
        return out

    @staticmethod
    def _build_watch_text(e: dict[str, Any]) -> tuple[str, str]:
        """(text, key tag) for one watchlist entry; ("", "") when there is nothing to say.
        The price alone is never the whole story: the user's buy conditions are spelled out."""
        name, price = e.get("name") or e["code"], e.get("price")
        if price is None:
            return "", ""
        band = (f"{e['buy_low']:g} 元" if e["buy_low"] == e["buy_high"]
                else f"{e['buy_low']:g} 到 {e['buy_high']:g} 元")  # fmt: skip
        conds = e.get("conditions") or []
        met = sum(1 for c in conds if c.get("state") == "met")
        need = e.get("conditions_needed") or len(conds)
        in_range, ready = e.get("status") == "in", e.get("condition_status") == "buy"
        lacking = list(dict.fromkeys(
            PLAIN_COND.get(str(c.get("metric")), str(c.get("label")))
            for c in conds if c.get("state") == "unmet"
        ))  # fmt: skip
        if in_range and not conds:
            return f"{name}今天收在 {price:.2f} 元，到了之前定的买入价（{band}）。", "in"
        if in_range and ready:
            return (f"{name}今天收在 {price:.2f} 元，到了买入价（{band}），之前定的买入条件"
                    f"也满足了（{met} 个，需要 {need} 个），可以考虑买了。", "buy")  # fmt: skip
        if in_range:
            why = f"还差：{'、'.join(lacking)}。" if lacking else ""
            return (f"{name}今天收在 {price:.2f} 元，到了买入价（{band}），但之前定的 "
                    f"{len(conds)} 个买入条件只满足了 {met} 个（需要 {need} 个）。{why}"
                    "先别急着买。", f"in:{met}")  # fmt: skip
        if ready:
            return (f"{name}：之前定的买入条件满足了（{met} 个，需要 {need} 个），"
                    f"但价格 {price:.2f} 元还没到买入价（{band}），继续等。", "ready")  # fmt: skip
        return "", ""

    @staticmethod
    def _list_futures(doc: dict[str, Any], full: bool) -> list[Alert]:
        flags = doc.get("flags") or []
        new = {f["key"] for f in flags} if full else set(doc.get("new_flags") or [])
        out = AlertMessageBuilder._list_reversions(doc, new)
        shown_flags = [f for f in flags if f["key"] in new and f.get("kind") != "reversion"]
        names = list(dict.fromkeys(f["name"] for f in shown_flags))
        if not names:
            return out
        shown = "、".join(names[:FUTURES_NAMED]) + (
            f"等 {len(names)} 个品种" if len(names) > FUTURES_NAMED else ""
        )
        text = f"期货：{shown}的价格出现一年里少见的变化，详情看 App。"
        keys = ",".join(sorted(k for k in new if not k.startswith("reversion:")))
        return [*out, Alert(f"fut:{doc.get('as_of', '')}:{keys}", "futures", text)]

    @staticmethod
    def _list_reversions(doc: dict[str, Any], new: set[str]) -> list[Alert]:
        out = []
        for s in doc.get("spreads") or []:
            key, z = f"reversion:{s['key']}", s.get("z_1y")
            if key not in new or z is None:
                continue
            name = s["name"].split("（")[0]
            side = "比平时高很多" if z > 0 else "比平时低很多"
            hl = s.get("half_life_d")
            back = f"，以前一般{AlertMessageBuilder._format_days(hl)}会回到正常" if hl else ""
            text = f"{name}{side}（{s['value']:,.0f} 元/吨）{back}。"
            out.append(Alert(f"{key}:{doc.get('as_of', '')}", "futures", text))
        return out

    @staticmethod
    def _format_days(sessions: int) -> str:
        if sessions <= FEW_WEEKS:
            return "两三周内"
        return f" {round(sessions / MONTH_SESSIONS)} 个月左右"

    @staticmethod
    def _list_macro(doc: dict[str, Any], full: bool) -> list[Alert]:
        out = []
        new = set(MACRO_KEYS) if full else set(doc.get("new_prints") or [])
        for s in doc.get("series") or []:
            key, v, month = s["key"], s.get("value"), s.get("month") or ""
            if key not in MACRO_KEYS or key not in new or v is None or len(month) != MONTH_LEN:
                continue
            m = int(month[4:6])
            if key == "cpi":
                feel = "比去年还便宜" if v < 0 else "还算平稳" if v < CPI_CALM else "涨得有点快"
                way = "涨" if v >= 0 else "跌"
                text = f"国家公布了 {m} 月物价：比去年同期{way} {abs(v):.1f}%，{feel}。"
            elif key == "ppi":
                feel = (
                    "原材料涨价压力大"
                    if v >= PPI_PRESSURE
                    else "工厂卖价在下降"
                    if v < 0
                    else "变化不大"
                )
                text = f"{m} 月工厂出厂价格比去年{'涨' if v >= 0 else '跌'} {abs(v):.1f}%，{feel}。"
            else:
                up = v >= PMI_LINE
                text = (f"{m} 月制造业景气指数 {v:.1f}，{'高于' if up else '低于'} 50，"
                        f"说明工厂生意{'在变好' if up else '在变差'}。")  # fmt: skip
            shot = CardShot("#macro", f".mc-card[data-series={key}]", f"macro_{key}",
                            PLAIN_MACRO.get(key, ""))  # fmt: skip
            out.append(Alert(f"macro:{key}:{month}", "macro", text, shot))
        return out
