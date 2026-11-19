"""Contract tests for visualization.AlertMessageBuilder (plan 22, D-153)."""

from __future__ import annotations

from typing import Any

from quant_cn.visualization.alert_message_builder import Alert, AlertMessageBuilder

ALL = ["volatility", "watchlist", "futures", "macro"]
CN = ["A股"]


def build_docs() -> dict[str, Any]:
    vol = {"lines": [{"key": "cn_300", "name": "300ETF VIX", "group": "A股", "value": 25.0,
                      "median": 18.9, "chg_pct": 0.05},
                     {"key": "us_vix", "name": "美国 VIX", "group": "美国", "value": 28.2,
                      "median": 17.1, "chg_pct": 0.42}],
           "flags": [{"key": "cn_300:pct", "kind": "pct"},
                     {"key": "us_vix:level", "kind": "level"},
                     {"key": "us_vix:jump", "kind": "jump"}]}  # fmt: skip
    wl = {"entries": [
        {"code": "601398.SH", "name": "工商银行", "price": 7.98, "buy_low": 7.4, "buy_high": 8.0,
         "status": "in", "condition_status": "wait", "conditions": []},
        {"code": "601888.SH", "name": "中国中免", "price": 50.0, "buy_low": 44.0, "buy_high": 48.0,
         "status": "near", "condition_status": "buy",
         "conditions": [{"state": "met"}, {"state": "met"}, {"state": "unmet"}]},
        {"code": "002032.SZ", "name": "苏泊尔", "price": 45.0, "buy_low": 40.0, "buy_high": 40.0,
         "status": "far", "condition_status": "wait", "conditions": []},
    ]}  # fmt: skip
    fut = {"as_of": "20261113", "new_flags": ["CU.SHF:curve"],
           "flags": [{"key": "CU.SHF:curve", "name": "铜"},
                     {"key": "AL.SHF:curve", "name": "铝"}]}  # fmt: skip
    macro = {"new_prints": ["cpi", "m2"],
             "series": [{"key": "cpi", "value": 0.7, "month": "202611"},
                        {"key": "m2", "value": 8.0, "month": "202610"}]}  # fmt: skip
    return {"volatility_monitor": vol, "watchlist": wl, "futures_monitor": fut,
            "macro_monitor": macro}  # fmt: skip


# TC-AMB-001
def test_tc_amb_001_lines() -> None:
    alerts = AlertMessageBuilder(ALL, CN).list_alerts(build_docs())
    by = {a.key: a for a in alerts}
    assert list(by) == ["vol:cn_300:pct", "wl:601398.SH:in", "wl:601888.SH:ready",
                        "fut:20261113:CU.SHF:curve", "macro:cpi:202611"]  # fmt: skip
    vol = by["vol:cn_300:pct"]
    assert vol.text == "A股沪深300的「恐慌指数」升到 25，平时在 19 左右，市场比较紧张。"
    assert vol.shot is not None and vol.shot.selector == ".mc-card[data-series=cn_300]"
    assert vol.shot.title == "A股沪深300恐慌指数"
    assert by["macro:cpi:202611"].shot.title == "物价（比去年）"  # type: ignore[union-attr]
    assert "到了之前定的买入价（7.4 到 8 元）" in by["wl:601398.SH:in"].text
    assert "买入条件满足了（2 个，需要 3 个）" in by["wl:601888.SH:ready"].text
    assert by["fut:20261113:CU.SHF:curve"].text.startswith("期货：铜的价格")
    assert "VIX" not in "".join(a.text for a in alerts)  # no English abbreviations
    assert "涨 0.7%，还算平稳" in by["macro:cpi:202611"].text


# TC-AMB-002
def test_tc_amb_002_off_and_missing() -> None:
    docs = build_docs()
    assert AlertMessageBuilder(["macro"], CN).list_alerts({**docs, "macro_monitor": None}) == []
    us_only = AlertMessageBuilder(["volatility"], ["A股"]).list_alerts(docs)
    assert [a.key for a in us_only] == ["vol:cn_300:pct"]  # 美国 line left out
    docs["futures_monitor"]["new_flags"] = []
    assert [a.trigger for a in AlertMessageBuilder(["futures"], CN).list_alerts(docs)] == []


# TC-AMB-003
def test_tc_amb_003_compose() -> None:
    alerts = [Alert(f"k{i}", "macro", f"第{i}条") for i in range(3)]
    text = AlertMessageBuilder.build_message(alerts, "20261113", 2)
    assert text == "【今日提醒 11月13日】\n· 第0条\n· 第1条\n还有 1 条，详见 App。"


# TC-AMB-004
def test_tc_amb_004_watchlist_wording() -> None:
    def entry(**kw: Any) -> dict[str, Any]:
        base = {"code": "600176.SH", "name": "中国巨石", "price": 27.37, "buy_low": 27.0,
                "buy_high": 30.0, "status": "in", "condition_status": "wait", "conditions": [],
                "conditions_needed": None}  # fmt: skip
        return base | kw

    conds = [{"metric": "sm_weeks_neg_4w", "state": "unmet"},
             {"metric": "retail_gauge", "state": "unmet"},
             {"metric": "lg_weeks_pos_4w", "state": "unmet"},
             {"metric": "custom", "label": "自定义条件", "state": "unmet"},
             {"metric": "close", "state": "met"}]  # fmt: skip
    b = AlertMessageBuilder(["watchlist"], CN)

    def one(**kw: Any) -> list[Alert]:
        return b.list_alerts({"watchlist": {"entries": [entry(**kw)]}})

    waiting = one(conditions=conds)[0]
    assert waiting.key == "wl:600176.SH:in:1"
    assert "5 个买入条件只满足了 1 个（需要 5 个）" in waiting.text
    assert "还差：散户还没离开、大户资金还没连续买入、自定义条件。先别急着买。" in waiting.text
    ready = one(conditions=conds, condition_status="buy", conditions_needed=1)[0]
    assert ready.key == "wl:600176.SH:buy" and ready.text.endswith("可以考虑买了。")
    above = one(conditions=conds, condition_status="buy", status="near", conditions_needed=1)
    assert above[0].key == "wl:600176.SH:ready" and "还没到买入价" in above[0].text
    assert one(conditions=conds, status="far") == []


# TC-AMB-005
def test_tc_amb_005_full_set() -> None:
    docs = build_docs()
    docs["volatility_monitor"]["flags"] = []
    docs["futures_monitor"]["new_flags"] = []
    docs["macro_monitor"]["new_prints"] = []
    full = AlertMessageBuilder(ALL, CN).list_alerts(docs, full=True)
    keys = [a.key for a in full]
    assert keys[0] == "vol:status" and "macro:cpi:202611" in keys
    status = full[0].text
    assert (
        status.startswith("A股「恐慌指数」现在：沪深300 25（平时 19，偏高）")
        and "美国" not in status
    )
    fut = next(a for a in full if a.trigger == "futures")
    assert fut.text.startswith("期货：铜、铝的价格")
    text = AlertMessageBuilder.build_message(full, "20261113", 8, sample=True)
    assert text.split("\n")[1].startswith("（这是自动提醒的样例")
    assert AlertMessageBuilder(ALL, CN).list_alerts(docs) == [
        a for a in full if a.trigger == "watchlist"
    ]


# TC-AMB-006
def test_tc_amb_006_reversion_line() -> None:
    docs = build_docs()
    fut = docs["futures_monitor"]
    name = "甲醇制烯烃利润（PP − 3×甲醇）"
    fut["spreads"] = [{"key": "mto_margin", "name": name, "value": -700.0, "z_1y": -2.4,
                       "half_life_d": 94}]  # fmt: skip
    fut["flags"] = [*fut["flags"], {"key": "reversion:mto_margin", "kind": "reversion",
                                    "name": name, "message": "x"}]  # fmt: skip
    fut["new_flags"] = ["reversion:mto_margin"]
    alerts = AlertMessageBuilder(["futures"], CN).list_alerts(docs)
    assert [a.text for a in alerts] == [
        "甲醇制烯烃利润比平时低很多（-700 元/吨），以前一般 4 个月左右会回到正常。"
    ]
