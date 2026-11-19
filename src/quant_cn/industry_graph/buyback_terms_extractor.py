"""DeepSeek reads buyback plans and holder 增持 plans into their terms (plan 32 ph2, D-169)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from pydantic import Field

from quant_cn.industry_graph.base_quoted_extractor import BaseQuotedExtractor, QuotedItem

KINDS = ("回购", "增持")
PURPOSES = ("注销", "员工持股", "股权激励", "维护价值", "转债转股", "其他")
HOLDER_TYPES = ("控股股东", "实控人", "一致行动人", "董监高", "持股5%以上股东", "国资平台",
                "核心员工", "其他")  # fmt: skip
FUNDINGS = ("自有", "自筹", "专项贷款", "其他")
METHODS = ("集中竞价", "大宗交易", "要约", "其他")
UNITS = {"元": 1.0, "万元": 1e4, "亿元": 1e8}
FIRST_PAGES = 3
LOAN_WORDS = re.compile(r"专项贷款|贷款承诺|借款")
LOAN_PAGES = 2


class BuybackTermsItem(QuotedItem):
    """
    Purpose:
        The terms of one buyback or 增持 plan as the model read them, before the checks.

    Contract:
        Input:
            kind: str (KINDS); purpose, holder_type, holders, funding: list[str];
            loan_bank: str | None; loan_amount: float | None; loan_unit: str | None;
            amount_low, amount_high: float | None; amount_unit: str | None;
            shares_low, shares_high, ratio_low, ratio_high, price_cap, period_months:
            float | None; method: str | None; quote; page
        Output:
            pydantic model (unknown keys ignored, numeric text parsed)
        Raises:
            pydantic.ValidationError  -- wrong types

    Used by:
        industry_graph.BuybackTermsExtractor  -- item_model

    Test cases:
        TC-BTX-001  (via BuybackTermsExtractor) items kept and dropped
    """

    kind: str
    purpose: list[str] = Field(default_factory=list)
    holder_type: list[str] = Field(default_factory=list)
    holders: list[str] = Field(default_factory=list)
    funding: list[str] = Field(default_factory=list)
    loan_bank: str | None = None
    loan_amount: float | None = None
    loan_unit: str | None = None
    amount_low: float | None = None
    amount_high: float | None = None
    amount_unit: str | None = None
    shares_low: float | None = None
    shares_high: float | None = None
    ratio_low: float | None = None
    ratio_high: float | None = None
    price_cap: float | None = None
    period_months: float | None = None
    method: str | None = None


class BuybackTermsExtractor(BaseQuotedExtractor):
    """
    Purpose:
        Turn a buyback plan (回购方案 / 预案 / 回购报告书) or a holder 增持计划 announcement into
        quote-checked terms (plan 32 ph2, D-169): kind 回购 / 增持, buyback purpose or 增持 holder
        type and names, funding (自有 / 自筹 / 专项贷款 with bank and loan amount), amount range,
        share and ratio range, price cap, period and method. Amounts are stored in yuan
        (amount_unit / loan_unit 元, 万元, 亿元 applied in code, never by the model). The pages
        sent are the first FIRST_PAGES plus up to LOAN_PAGES later pages that mention a loan.
        An item is kept when its kind is known and it has an amount, share or ratio range;
        label values outside the allowed lists become "其他" (purpose, holder type, funding)
        or None (method), and purpose / holder fields of the other kind are emptied.

    Contract:
        Input:
            llm: BaseLlmClient; max_chars: int > 0; system: str | None
            (default prompts/buyback_terms_extraction.txt)
        Output:
            instance; `list_pages`, `check_item`, `fetch_items` (BaseQuotedExtractor)
        Raises:
            (none at construction)

    Used by:
        lake meta/runs/plan32_terms.py (plan 32 phase 2 pilot and full run)

    Test cases:
        TC-BTX-001  valid reply: amounts in 万元 / 亿元 stored in yuan, unknown labels mapped to
                    其他, the other kind's fields emptied; unknown kind and an item without any
                    range dropped
        TC-BTX-002  list_pages keeps the first FIRST_PAGES pages and later loan pages, in order
        TC-BTX-003  an unknown amount unit drops the amounts, not the item when shares remain
    """

    PROMPT_FILE = "buyback_terms_extraction.txt"

    @property
    def item_model(self) -> type[QuotedItem]:
        """
        Purpose:
            The reply item model.

        Contract:
            Input:
                (none)
            Output:
                type[QuotedItem]  -- BuybackTermsItem
            Raises:
                (none)
        """
        return BuybackTermsItem

    def list_pages(self, pages: Sequence[str]) -> list[tuple[int, str]]:
        """
        Purpose:
            The first FIRST_PAGES pages plus up to LOAN_PAGES later pages with loan words.

        Contract:
            Input:
                pages: Sequence[str]
            Output:
                list[tuple[int, str]]  -- (page from 1, text), in page order
            Raises:
                (none)
        """
        head = [(n, t) for n, t in enumerate(pages[:FIRST_PAGES], 1) if t.strip()]
        rest = self.list_top_pages(pages[FIRST_PAGES:], LOAN_WORDS, LOAN_PAGES)
        return head + [(n + FIRST_PAGES, t) for n, t in rest]

    def check_item(self, item: QuotedItem) -> dict[str, Any] | None:
        """
        Purpose:
            The stored terms of an item with a known kind and a range, amounts in yuan.

        Contract:
            Input:
                item: QuotedItem
            Output:
                dict[str, Any] | None  -- None for an unknown kind or no amount / share /
                                          ratio range; amount_unit and loan_unit removed
            Raises:
                (none)
        """
        if not isinstance(item, BuybackTermsItem) or item.kind not in KINDS:
            return None
        row = item.model_dump(exclude={"quote", "page", "amount_unit", "loan_unit"})
        scale = UNITS.get(item.amount_unit or "")
        row["amount_low"] = self._compute_yuan(item.amount_low, scale)
        row["amount_high"] = self._compute_yuan(item.amount_high, scale)
        row["loan_amount"] = self._compute_yuan(item.loan_amount, UNITS.get(item.loan_unit or ""))
        ranges = ("amount_low", "amount_high", "shares_low", "shares_high", "ratio_low",
                  "ratio_high")  # fmt: skip
        if all(row[k] is None for k in ranges):
            return None
        buyback = item.kind == "回购"
        row["purpose"] = self._build_labels(item.purpose, PURPOSES) if buyback else []
        row["holder_type"] = [] if buyback else self._build_labels(item.holder_type, HOLDER_TYPES)
        row["holders"] = [] if buyback else [h.strip() for h in item.holders if h.strip()]
        row["funding"] = self._build_labels(item.funding, FUNDINGS)
        row["method"] = item.method if item.method in METHODS else None
        return row

    @staticmethod
    def _compute_yuan(value: float | None, scale: float | None) -> float | None:
        return None if value is None or scale is None else value * scale

    @staticmethod
    def _build_labels(values: Sequence[str], allowed: Sequence[str]) -> list[str]:
        out: list[str] = []
        for value in values:
            label = value if value in allowed else "其他"
            if label not in out:
                out.append(label)
        return out
