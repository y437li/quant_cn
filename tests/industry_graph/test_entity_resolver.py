from __future__ import annotations

from quant_cn.industry_graph.entity_resolver import EntityResolver

FULL = [
    ("300750.SZ", "宁德时代新能源科技股份有限公司"),
    ("600941.SH", "中国移动有限公司"),
    ("002588.SZ", "史丹利农业集团股份有限公司"),
    ("601127.SH", "赛力斯集团股份有限公司"),
]
SHORT = [("300750.SZ", "宁德时代"), ("600941.SH", "中国移动"), ("002588.SZ", "史丹利"),
         ("601127.SH", "赛力斯"), ("601127.SH", "小康股份"), ("000001.SZ", "环球"),
         ("000002.SZ", "环球"), ("600000.SH", "*ST长城")]  # fmt: skip
ALIASES = {"华为技术有限公司": "x:华为", "LGES": "x:LG新能源"}


def build() -> EntityResolver:
    return EntityResolver(FULL, SHORT, ALIASES)


# TC-ER-001
def test_tc_er_001_methods() -> None:
    r = build()
    got = {n: (m.entity_id, m.method) for n in [
        "宁德时代新能源科技股份 有限公司", "宁德时代", "小康股份", "华为技术有限公司", "lges",
        "中国移动通信集团广东有限公司", "长城", "特斯拉", "宁德时代（上海）"]
        for m in [r.find_entity(n)]}  # fmt: skip
    assert got == {
        "宁德时代新能源科技股份 有限公司": ("a:300750.SZ", "full"),
        "宁德时代": ("a:300750.SZ", "short"),
        "小康股份": ("a:601127.SH", "short"),
        "华为技术有限公司": ("x:华为", "alias"),
        "lges": ("x:LG新能源", "alias"),
        "中国移动通信集团广东有限公司": ("a:600941.SH", "prefix"),
        "长城": ("a:600000.SH", "short"),
        "特斯拉": ("x:特斯拉", "unresolved"),
        "宁德时代（上海）": ("a:300750.SZ", "short"),
    }


# TC-ER-002
def test_tc_er_002_group_and_ambiguity() -> None:
    r = build()
    member = r.find_entity("中国移动及其关联方")
    assert (member.entity_id, member.method, member.is_group_member) == (
        "a:600941.SH",
        "full",
        True,
    )
    assert r.find_entity("赛力斯汽车有限公司").method == "unresolved"  # 3-character prefix
    assert r.find_entity("史丹利百得").method == "unresolved"
    assert r.find_entity("环球").method == "unresolved"  # two companies
    assert not r.find_entity("宁德时代").is_group_member


# TC-ER-003
def test_tc_er_003_build_key() -> None:
    assert EntityResolver.build_key(" Tesla, Inc. ") == "tesla"
    assert EntityResolver.build_key("宁德时代（上海）有限公司") == "宁德时代(上海)"
    assert EntityResolver.build_key("") == ""


# TC-ER-004
def test_tc_er_004_find_by_code() -> None:
    r = EntityResolver(FULL, [*SHORT, ("000725.SZ", "京东方A")])
    hit = r.find_by_code("京东方", "000725.SZ")
    assert hit is not None and (hit.entity_id, hit.method) == ("a:000725.SZ", "code")
    assert r.find_by_code("宁德时代新能源", "300750.SZ") is not None
    assert r.find_by_code("京东方", "999999.SZ") is None
    assert r.find_by_code("比亚迪", "300750.SZ") is None


# TC-ER-005
def test_tc_er_005_member_names() -> None:
    r = EntityResolver(FULL, SHORT, {"上汽乘用车": "a:600104.SH"}, member_names=["上汽乘用车"])
    hit = r.find_entity("上汽乘用车")
    assert (hit.entity_id, hit.method, hit.is_group_member) == ("a:600104.SH", "alias", True)
    assert not build().find_entity("华为技术有限公司").is_group_member


# TC-ER-006
def test_tc_er_006_former_names() -> None:
    r = EntityResolver(
        FULL,
        [("601727.SH", "上海电气")],
        former_names=[("600835.SH", "上海电气"), ("600077.SH", "国能集团")],
    )
    now = r.find_entity("上海电气")
    assert (now.entity_id, now.method) == ("a:601727.SH", "short")
    old = r.find_entity("国能集团")
    assert (old.entity_id, old.method) == ("a:600077.SH", "former")


# TC-ER-007
def test_tc_er_007_member_code() -> None:
    r = EntityResolver(
        [*FULL, ("601238.SH", "广州汽车集团股份有限公司")], [*SHORT, ("601238.SH", "广汽集团")]
    )
    assert r.find_by_code("埃安", "601238.SH") is None
    hit = r.find_by_code("埃安", "601238.SH", is_member=True)
    assert hit is not None and (hit.method, hit.is_group_member) == ("member_code", True)
    assert r.find_by_code("埃安", "999999.SH", is_member=True) is None


# TC-ER-008
def test_tc_er_008_find_by_alias() -> None:
    r = EntityResolver([*FULL, ("002558.SZ", "巨人网络集团股份有限公司")],
                       [*SHORT, ("002558.SZ", "巨人网络")])  # fmt: skip
    hit = r.find_by_alias("上海巨人网络科技有限公司", "巨人网络", None, "巨人网络")
    assert hit is not None and hit.ts_code == "002558.SZ" and hit.is_group_member
    assert hit.name == "上海巨人网络科技有限公司"
    by_code = r.find_by_alias("巨人", "巨人", "002558.SZ", None)
    assert by_code is not None and by_code.method == "code"
    member = r.find_by_alias("征途工作室", "征途", None, "巨人网络")
    assert member is not None and member.method == "member_code"
    assert r.find_by_alias("腾讯天美", "腾讯", "0700.HK", "腾讯控股") is None
    assert r.find_by_alias("某工作室", "某工作室", None, "不存在集团") is None
