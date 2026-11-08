from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from quant_cn.core.exceptions import DataSourceError
from quant_cn.industry_graph.annual_report_parser import AnnualReportParser
from quant_cn.industry_graph.counterparty_table_parser import (
    CounterpartyRow,
    CounterpartyTable,
    CounterpartyTableParser,
)
from quant_cn.industry_graph.pdf_text_extractor import PdfTextExtractor, ReportPages
from quant_cn.industry_graph.section_detector import SectionDetector

HEADER = "示例科技股份有限公司2025 年年度报告全文"

# SZSE layout (宁德时代-style, 千元), as PdfTextExtractor returns it: one value per line
SZSE = """（8）主要销售客户和主要供应商情况
公司主要销售客户情况
前五名客户合计销售金额（千元）
165,061,533
前五名客户合计销售金额占年度销售总额比例
38.96%
公司前5 大客户资料
序号
客户名称
销售额（千元）
占年度销售总额比例
1
第一名
58,159,202
13.73%
2
第二名
47,127,609
11.12%
3
第三名
30,201,701
7.13%
4
第四名
15,419,319
3.64%
5
第五名
14,153,702
3.34%
合计
--
165,061,533
38.96%
公司主要供应商情况
前五名供应商合计采购金额（千元）
993,090
前五名供应商合计采购金额占年度采购总额比例
20.64%
公司前5 名供应商资料
序号
供应商名称
采购额（千元）
占年度采购总额比例
1
金氏铜业有限公司
259,770
5.40%
2
江西铜业股份有限公司
223,369
4.64%
3
惠州联电电工材料有限公司
217,447
4.52%
4
广东华创盈五金科技有限公司
158,714
3.30%
5
DZC OPTOELECTRONICS TECHNOLOGY (VIET NAM)
COMPANY LIMITED
133,791
2.78%
合计
--
993,091
20.64%
3、费用"""

STAR = """A.公司主要销售客户情况
前五名客户销售额83,702.77万元，占年度销售总额57.14%；其中前五名客户销售额中关联方销售额0万元。
公司前五名客户
单位：万元 币种：人民币
序号 客户名称 销售额 占年度销售总额比例 （%） 是否与上市公司存在 关联关系
1 客户一 29,548.35 20.17 否
2 客户二 18,534.53 12.65 否
3 客户三 13,979.42 9.54 否
4 客户四 12,311.29 8.40 否
5 客户五 9,329.18 6.37 否
合计 / 83,702.77 57.13 /
B.公司主要供应商情况
前五名供应商采购额65,479.88万元，占年度采购总额42.99%；其中前五名供应商采购额中关联方采购额0万元。
公司前五名供应商
单位：万元 币种：人民币
序号 供应商名称 采购额 占年度采购总额比例 （%） 是否与上市公司存在 关联关系
1 供应商一 25,997.75 17.07 否
2 供应商二 11,722.49 7.70 否
3 供应商三 10,783.45 7.08 否
4 供应商四 9,522.70 6.25 否
5 供应商五 7,453.50 4.89 否
合计 / 65,479.88 42.99 /"""

SSE_MAIN = """(7). 主要销售客户及主要供应商情况
A.公司主要销售客户及主要供应商情况
前五名客户销售额1,762,423.77万元，占年度销售总额55.72%；其中前五名客户销售额中关联方销售额0万元。
前五名供应商采购额127,960.25万元，占年度采购总额26.61%；其中前五名供应商采购额中关联方采购额0万元。
3、费用"""


def build_pages(counterparty_text: str = SZSE) -> ReportPages:
    pages = [
        "目录\n第一节 重要提示\n第二节 公司简介\n第三节 管理层讨论与分析\n第四节 公司治理",
        "第一节 重要提示、目录和释义\n公司已在本报告的“第三节管理层讨论与分析”中描述风险。",
        "第三节 管理层讨论与分析\n一、报告期内公司从事的主要业务\n公司主要产品为动力电池。",
        "二、报告期内公司所处行业情况\n新能源汽车行业快速增长。",
        "四、主营业务分析\n营业收入构成\n" + counterparty_text,
        "第四节 公司治理\n董事会运作。",
        "财务报告附注" * 20,
    ]
    return ReportPages(pages)


def write_pdf(path: Path, bodies: list[str]) -> None:
    doc = pymupdf.open()
    for i, body in enumerate(bodies, start=1):
        page = doc.new_page()
        page.insert_text((50, 40), HEADER, fontname="china-s", fontsize=9)
        page.insert_text((50, 100), body, fontname="china-s", fontsize=11)
        page.insert_text((290, 800), str(i), fontname="helv", fontsize=9)
    doc.set_toc([[1, "第三节 管理层讨论与分析", 2]])
    doc.save(path)


# TC-PTE-001
def test_tc_pte_001_headers_removed(tmp_path: Path) -> None:
    path = tmp_path / "r.pdf"
    write_pdf(
        path, ["第一节 重要提示", "第三节 管理层讨论与分析", "1\n第一名\n13.73%", "第四节 公司治理"]
    )
    report = PdfTextExtractor().read_pages(path)
    assert len(report.pages) == 4 and report.outline == [(1, "第三节 管理层讨论与分析", 2)]
    assert all(HEADER.replace(" ", "") not in p.replace(" ", "") for p in report.pages)
    assert report.pages[2].splitlines() == ["1", "第一名", "13.73%"]
    assert report.n_chars == sum(len(p) for p in report.pages)


# TC-PTE-002
def test_tc_pte_002_rare_lines_and_short_docs_kept() -> None:
    extractor = PdfTextExtractor()
    pages = [f"{HEADER}\n正文{i}\n1\n客户一" for i in range(4)]
    pages[0] += "\n只出现一次的行"
    cleaned = extractor.normalize_pages(pages)
    assert cleaned[0].splitlines() == ["正文0", "1", "客户一", "只出现一次的行"]
    assert extractor.normalize_pages(["页眉文字\n正文", "页眉文字\n正文"]) == [
        "页眉文字\n正文",
        "页眉文字\n正文",
    ]
    with pytest.raises(ValueError):
        PdfTextExtractor(header_share=0)


# TC-PTE-003
def test_tc_pte_003_unreadable(tmp_path: Path) -> None:
    with pytest.raises(DataSourceError):
        PdfTextExtractor().read_pages(tmp_path / "missing.pdf")
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"<html>")
    with pytest.raises(DataSourceError):
        PdfTextExtractor().read_pages(bad)


# TC-SD-001
def test_tc_sd_001_chapter_and_sections() -> None:
    sections = SectionDetector().list_sections(build_pages())
    assert [(s.key, s.page_start, s.page_end) for s in sections] == [
        ("chapter", 3, 5),
        ("business", 3, 3),
        ("industry", 4, 4),
        ("revenue_mix", 5, 5),
        ("counterparties", 5, 5),
    ]


# TC-SD-002
def test_tc_sd_002_no_chapter() -> None:
    report = ReportPages(["目录", "正文", "第四节 公司治理"])
    assert SectionDetector().find_chapter(report) is None
    assert SectionDetector().list_sections(report) == []


# TC-SD-003
def test_tc_sd_003_missing_heading_omitted() -> None:
    sections = SectionDetector().list_sections(build_pages(counterparty_text="无"))
    keys = [s.key for s in sections]
    assert keys[0] == "chapter" and "counterparties" not in keys and "risks" not in keys


# TC-CTP-001
def test_tc_ctp_001_szse() -> None:
    customers, suppliers = CounterpartyTableParser().parse_tables(SZSE)
    assert customers.total_amount == pytest.approx(165_061_533e3)
    assert customers.total_share_pct == 38.96
    assert [r.rank for r in customers.rows] == [1, 2, 3, 4, 5]
    assert customers.rows[0].amount == pytest.approx(58_159_202e3)
    assert suppliers.rows[1].name == "江西铜业股份有限公司"
    assert suppliers.rows[4].name == "DZC OPTOELECTRONICS TECHNOLOGY (VIET NAM) COMPANY LIMITED"
    assert suppliers.rows[4].share_pct == 2.78


# TC-CTP-002
def test_tc_ctp_002_star() -> None:
    customers, suppliers = CounterpartyTableParser().parse_tables(STAR)
    assert customers.total_amount == pytest.approx(83_702.77e4)
    assert customers.rows[0] == CounterpartyRow(1, "客户一", pytest.approx(29_548.35e4), 20.17)
    assert len(suppliers.rows) == 5 and suppliers.total_share_pct == 42.99


# TC-CTP-003
def test_tc_ctp_003_sse_main_sentence() -> None:
    customers, suppliers = CounterpartyTableParser().parse_tables(SSE_MAIN)
    assert customers.total_share_pct == 55.72 and not customers.rows
    assert customers.total_amount == pytest.approx(1_762_423.77e4)
    assert suppliers.total_share_pct == 26.61 and suppliers.total_amount == pytest.approx(
        127_960.25e4
    )


# TC-CTP-004
def test_tc_ctp_004_consistency_and_anonymity() -> None:
    customers, suppliers = CounterpartyTableParser().parse_tables(SZSE)
    assert customers.is_consistent and suppliers.is_consistent
    assert all(r.is_anonymous for r in customers.rows)
    assert not any(r.is_anonymous for r in suppliers.rows)
    assert CounterpartyRow(1, "客户 A", 1.0, 1.0).is_anonymous
    assert not CounterpartyTable("customer", 1.0, 10.0, []).is_consistent
    short = CounterpartyTable("customer", 1.0, 10.0, [CounterpartyRow(1, "客户一", 1.0, 5.0)])
    assert not short.is_consistent


# TC-CTP-005
def test_tc_ctp_005_no_block() -> None:
    customers, suppliers = CounterpartyTableParser().parse_tables("本节不涉及客户信息。")
    assert customers == CounterpartyTable("customer") and suppliers == CounterpartyTable("supplier")


def build_parser() -> AnnualReportParser:
    return AnnualReportParser(PdfTextExtractor(), SectionDetector(), CounterpartyTableParser())


# TC-ARP-001
def test_tc_arp_001_parse_pages() -> None:
    parsed = build_parser().parse_pages(Path("x.pdf"), build_pages())
    assert parsed.n_pages == 7 and 0 < parsed.chapter_share < 1
    counterparties = parsed.get_section("counterparties")
    assert counterparties is not None and counterparties.page_start == 5
    assert parsed.customers.is_consistent and parsed.suppliers.is_consistent


# TC-ARP-002
def test_tc_arp_002_no_chapter() -> None:
    parsed = build_parser().parse_pages(Path("x.pdf"), ReportPages(["正文"] * 3))
    assert parsed.sections == [] and parsed.chapter_share == 0.0
    assert not parsed.customers.rows and parsed.get_section("chapter") is None


BSE_PAGES = [
    "第四节\n管理层讨论与分析\n一、\n业务概要\n公司从事偏光片的研发、生产与销售。",
    "(3) 主要客户情况\n单位：元\n序\n号\n客户\n销售金额\n年度销售占比%\n是否存在关\n联关系\n"
    "1 客户1\n17,938,575.96\n8.43% 否\n2 客户2\n16,099,411.16\n7.56% 否\n"
    "3 客户3\n16,079,040.73\n7.55% 否\n4 客户4\n13,656,178.52\n6.42% 否\n"
    "5 客户5\n13,361,226.37\n6.28% 否\n合计\n77,134,432.74\n36.24%\n-\n"
    "(4) 主要供应商情况\n单位：元\n序号\n供应商\n采购金额\n年度采购占比%\n是否存在关联\n关系\n"
    "1\n供应商1\n14,149,134.28\n8.94% 否\n2\n供应商2\n12,184,842.46\n7.70% 否\n"
    "3\n供应商3\n11,736,729.64\n7.42% 否\n4\n供应商4\n10,323,371.79\n6.52% 否\n"
    "5\n供应商5\n5,708,738.39\n3.61% 否\n合计\n54,102,816.56\n34.19%\n-",
    "第五节 重大事件\n一、重大事件索引",
]


# TC-SD-004
def test_tc_sd_004_bse_and_ah_layouts() -> None:
    bse = SectionDetector().list_sections(ReportPages(BSE_PAGES))
    assert [(s.key, s.page_start, s.page_end) for s in bse] == [
        ("chapter", 1, 2),
        ("business", 1, 1),
        ("counterparties", 2, 2),
    ]
    ah = ReportPages(["目录", "第二章 董事会报告\n（3）主要客户、供应商", "第三章 公司治理"])
    assert SectionDetector().find_chapter(ah) == (2, 2)


# TC-SD-005
def test_tc_sd_005_find_heading_page() -> None:
    report = ReportPages(["第三节 管理层讨论与分析....... 9", "正文", "前五名客户销售额10万元"])
    assert SectionDetector().find_heading_page(report, "counterparties") == 3
    assert SectionDetector().find_heading_page(ReportPages(["正文"]), "counterparties") is None


# TC-CTP-006
def test_tc_ctp_006_bse() -> None:
    customers, suppliers = CounterpartyTableParser().parse_tables("\n".join(BSE_PAGES[1:]))
    assert customers.total_amount == pytest.approx(77_134_432.74)
    assert customers.total_share_pct == 36.24 and customers.is_consistent
    assert suppliers.rows[4] == CounterpartyRow(5, "供应商5", pytest.approx(5_708_738.39), 3.61)
    assert suppliers.is_consistent


# TC-CTP-007
def test_tc_ctp_007_sentence_variants() -> None:
    ah = (
        "向前五名客户合计的销售金额为60,084.6 百万元，占本集团销售总额的44.87%。"
        "向前五名供应商合计的采购金额为9,000 百万元，占本集团采购总额的12.5%。"
    )
    customers, suppliers = CounterpartyTableParser().parse_tables(ah)
    assert (
        customers.total_amount == pytest.approx(60_084.6e6) and customers.total_share_pct == 44.87
    )
    assert suppliers.total_share_pct == 12.5
    sinopec = (
        "对前五大供货商的采购额为人民币10,467.81 亿元，占本公司年度采购总额的44.57%。"
        "对本公司前五名主要客户的销售额为人民币2,189.59 亿元，占本公司年度销售总额的 7.87%。"
    )
    customers, suppliers = CounterpartyTableParser().parse_tables(sinopec)
    assert customers.total_share_pct == 7.87
    assert customers.total_amount == pytest.approx(2_189.59e8)


# TC-CTP-008
def test_tc_ctp_008_joint_heading_and_note() -> None:
    text = (
        "本公司前五名客户销售额及供应商采购额均为合并列示；前五名供应商中的客户1为同一控制。"
        "A.公司主要销售客户及主要供应商情况 前五名客户销售额99,204.82万元，占年度销售总额50.81%。"
        "前五名供应商采购额30,362.18万元，占年度采购总额27.82%。"
    )
    customers, suppliers = CounterpartyTableParser().parse_tables(text)
    assert customers.total_share_pct == 50.81 and suppliers.total_share_pct == 27.82


# TC-ARP-003
def test_tc_arp_003_block_outside_chapter() -> None:
    pages = ReportPages(["正文", "前五名客户销售额100万元，占年度销售总额20%。"])
    parsed = build_parser().parse_pages(Path("x.pdf"), pages)
    assert parsed.sections == [] and parsed.customers.total_share_pct == 20.0


# TC-CTP-009
def test_tc_ctp_009_wording_variants() -> None:
    text = (
        "前5名客户销售额8,564,005万元，占境内年度销售总额近100%。"
        "前五名客 户销售额24,098.32万元，占年度主营业务销售收入总额31.28%。"
    )
    customers, _ = CounterpartyTableParser().parse_tables(text)
    assert customers.total_share_pct == 100.0
    wrapped, _ = CounterpartyTableParser().parse_tables(text.split("。", 1)[1])
    assert wrapped.total_share_pct == 31.28


# TC-CTP-010
def test_tc_ctp_010_bse_rd_mention_and_bare_shares() -> None:
    text = (
        "公司持续加大研发投入。(3) 主要客户情况 单位：元 序号 客户 销售金额 年度销售占比% "
        "是否存在关联关系 1 A 54,045,125.35 10.06 否 2 B 39,099,120.16 7.28 否 "
        "合计 93,144,245.51 17.34 - (4) 主要供应商情况"
    )
    customers, _ = CounterpartyTableParser().parse_tables(text)
    assert [r.name for r in customers.rows] == ["A", "B"]
    assert customers.total_share_pct == 17.34
