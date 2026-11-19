"""Rules for a counterparty name an LLM returns: is it a real name, and is it in the text (ph2)."""

from __future__ import annotations

import re

# a name that only numbers a counterparty (客户一, 客户A, 第一名, 供应商甲, 客商9, 客户E及其关联方,
# H公司)
# or hides it (某)
ANONYMOUS = re.compile(
    r"^(?:前五名)?(?:第[一二三四五六七八九十0-9]+名?"
    r"|(?:客户|供应商|单位|公司|客商)[一二三四五六七八九十A-Za-z甲乙丙丁戊0-9]{1,3}名?)"
    r"(?:及其(?:关联方|关联公司|子公司|下属公司|下属单位))?$"
    r"|^[A-Za-z甲乙丙丁]{1,2}(?:公司|客户|供应商|集团|企业)$|某"
)
# a numbered or ranked counterparty anywhere in the name (应付账款-供应商7, 内销客户8, 客户(一),
# 2019年第1大客户, 第四名供应商, 法人一, 客户1子公司3), a rank phrase (排名第一的供应商), a masked
# name (天津**有限公司) or a single letter (P)
NUMBERED = re.compile(
    r"(?:客户|供应商|客商|单位|法人)[（(]?[一二三四五六七八九十0-9A-Za-z甲乙丙丁戊]{1,3}[）)]?"
    r"(?:名|子公司[0-9一二三四五六七八九十]*)?$"
    r"|第[一二三四五六七八九十0-9]+(?:名|大)(?:客户|供应商|客商)?"
    r"|排名第|\*\*|^[A-Za-z]$"
)
# not a counterparty at all: an empty cell, a bare role word, a code of 5+ digits (360, 1688 and
# 711 are brands), a place + 公司
PLACEHOLDER = re.compile(
    r"^(?:无|不适用|其他|其它|合计|小计|客户|供应商|经销商|终端客户|合作方|[0-9]{5,}"
    r"|(?:香港|台湾|澳门|美国|日本|韩国|德国|境外|海外|国外|国内)(?:子)?公司)$"
)
# a class of counterparties, not one (头部车企, 国内无人机厂商, 下游国际知名企业)
GENERIC = re.compile(
    r"^(?:国内外?|海外|境外|国际|全球|下游|上游|多家|部分|主要|头部|知名|大型|核心|重要|一线"
    r"|龙头|优质|若干|其他|相关|北美|欧洲|日韩)"
    r".*(?:客户|供应商|厂商|厂家|企业|车企|主机厂|制造商|品牌|运营商|公司|集团|机构|单位)$"
)
LEGAL_SUFFIX = re.compile(
    r"(?:股份有限公司|有限责任公司|有限公司|股份公司|集团公司|集团|公司"
    r"|co\.?,?ltd\.?|inc\.?|corp\.?|corporation|limited|llc|gmbh|ag)$"
)
REGION_PREFIX = re.compile(
    r"^[（(]?(?:中国|北京|上海|深圳|广州|广东|江苏|浙江|天津|重庆|香港)[)）]?"
)
SPACE = re.compile(r"\s+")
MIN_KEY_CHARS = 2  # one character matches by chance
CORE_PREFIX = 4  # a short form keeps the first characters of the name (宁德时代新能源… → 宁德时代)


class CounterpartyName:
    """
    Purpose:
        The two checks plan 28 applies to every customer / supplier / partner name an LLM
        returns (D-161 updates 8, 10): `is_named` (a real name, not a number like 客户一 / 供应商A /
        客商9, not hidden with 某, not a class like 头部车企 or 国内无人机厂商; a bare
        letter name such as GE or LG is a real name) and `is_in_text` (the name or its alias
        occurs in a text, whitespace and case ignored, also after removing the legal suffix
        or as its first CORE_PREFIX characters, with or without a leading region: 宁德时代 for
        宁德时代新能源科技股份有限公司).

    Contract:
        Input:
            (none; static methods)
        Output:
            `is_named(name) -> bool`, `is_in_text(name, alias, text) -> bool`
        Raises:
            (none)

    Used by:
        industry_graph.InquiryCustomerExtractor  -- is_named flag and name-in-quote check
        industry_graph.IrCustomerExtractor  -- drops unnamed rows; name-in-quote check
        industry_graph.CompanyEdgeBuilder  -- drops unnamed counterparties

    Test cases:
        TC-CPN-001  is_named: 客户一, 供应商A, 客商9, 第一名, 供应商B及其关联方, H公司, 西安某科技,
                    头部车企, 国内无人机厂商
                    are not named; 宁德时代, GE and LG Energy Solution are
        TC-CPN-002  is_in_text: full name, alias, suffix-stripped and 4-character short form
                    found; a name absent from the text is not; empty name is not
        TC-CPN-003  is_named: numbered or ranked names anywhere (应付账款-供应商7, 内销客户8,
                    客户(一), 2019年第1大客户, 第四名供应商, 法人一, 客户1 子公司3, 排名第一的
                    供应商, 天津**有限公司, P) and
                    placeholders (无, 客户, 100905, 香港公司) are not named; 华为公司, 第一创业,
                    客户关系管理软件公司, 360, 1688, 7-11 are
    """

    @staticmethod
    def is_named(name: str) -> bool:
        """
        Purpose:
            True when the name identifies one counterparty.

        Contract:
            Input:
                name: str
            Output:
                bool
            Raises:
                (none)
        """
        text = SPACE.sub("", name)
        if not text or PLACEHOLDER.match(text):
            return False
        rules = (ANONYMOUS, GENERIC, NUMBERED)
        return not any(rule.search(text) for rule in rules)

    @staticmethod
    def is_in_text(name: str, alias: str | None, text: str) -> bool:
        """
        Purpose:
            True when the name (or its alias, or its short form) occurs in the text.

        Contract:
            Input:
                name: str; alias: str | None; text: str
            Output:
                bool
            Raises:
                (none)
        """
        haystack = SPACE.sub("", text).lower()
        full = SPACE.sub("", name).lower()
        core = CounterpartyName._build_core(full)
        short = {core[:CORE_PREFIX], REGION_PREFIX.sub("", core)[:CORE_PREFIX]}
        keys = {full, core, SPACE.sub("", alias or "").lower()} | short
        return any(len(k) >= MIN_KEY_CHARS and k in haystack for k in keys)

    @staticmethod
    def _build_core(name: str) -> str:
        previous = None
        while previous != name:
            previous, name = name, LEGAL_SUFFIX.sub("", name)
        return name
