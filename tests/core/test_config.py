from __future__ import annotations

from pathlib import Path

import pytest

from quant_cn.core.config import Config
from quant_cn.core.exceptions import ConfigError

REPO = Path(__file__).resolve().parents[2]


# TC-C-001
def test_tc_c_001_lake_root_precedence(repo: Path, tmp_path: Path) -> None:
    assert Config.load(repo, env={}).lake.root == (Path.home() / "quant_cn_lake").resolve()
    (repo / "config" / "local.yaml").write_text(f"lake:\n  root: {tmp_path / 'local'}\n")
    assert Config.load(repo, env={}).lake.root == (tmp_path / "local").resolve()
    env = {"QUANT_CN_LAKE_ROOT": str(tmp_path / "env")}
    assert Config.load(repo, env=env).lake.root == (tmp_path / "env").resolve()


# TC-C-002
def test_tc_c_002_token_from_env_only(repo: Path, tmp_path: Path) -> None:
    base = repo / "config" / "base.yaml"
    base.write_text(base.read_text().replace("tushare:\n", "tushare:\n  token: from-yaml\n"))
    env = {"QUANT_CN_LAKE_ROOT": str(tmp_path), "TUSHARE_TOKEN": "secret-token"}
    config = Config.load(repo, env=env)
    assert config.tushare.token == "secret-token"
    assert "secret-token" not in repr(config)


# TC-C-003
def test_tc_c_003_inside_repo_refused(repo: Path) -> None:
    with pytest.raises(ConfigError):
        Config.load(repo, env={"QUANT_CN_LAKE_ROOT": str(repo / "data")})
    (repo / "config" / "local.yaml").write_text("lake:\n  allow_inside_repo: true\n")
    config = Config.load(repo, env={"QUANT_CN_LAKE_ROOT": str(repo / "data")})
    assert config.lake.root == (repo / "data").resolve()


# TC-C-004
def test_tc_c_004_start_for(config: Config) -> None:
    assert config.get_start("trade_cal") == "19901219"
    assert config.get_start("daily") == config.download.long_history_start
    assert config.get_start("moneyflow") == config.download.default_start
    assert config.get_start("daily_basic") == "20180901"  # own start wins


# TC-C-005
def test_tc_c_005_unknown_dataset(config: Config) -> None:
    with pytest.raises(ConfigError):
        config.get_dataset("nope")


# TC-C-006
def test_tc_c_006_root_resolution(repo: Path) -> None:
    assert (
        Config.load(repo, env={"QUANT_CN_LAKE_ROOT": "~/x_lake"}).lake.root
        == Path.home() / "x_lake"
    )
    (repo / "config" / "local.yaml").write_text("lake:\n  root: ../sibling_lake\n")
    assert Config.load(repo, env={}).lake.root == (repo.parent / "sibling_lake").resolve()


# TC-C-007
def test_tc_c_007_committed_config_loads(tmp_path: Path) -> None:
    config = Config.load(REPO, env={"QUANT_CN_LAKE_ROOT": str(tmp_path)})
    assert all(name in config.datasets for name in config.download.order)


# TC-C-008
def test_tc_c_008_malformed_config(repo: Path, tmp_path: Path) -> None:
    env = {"QUANT_CN_LAKE_ROOT": str(tmp_path)}
    (repo / "config" / "local.yaml").write_text("lake: [unclosed\n")
    with pytest.raises(ConfigError):
        Config.load(repo, env=env)
    (repo / "config" / "local.yaml").unlink()
    datasets = repo / "config" / "datasets.yaml"
    datasets.write_text(
        datasets.read_text().replace("daily:\n  endpoint", "daily:\n  name: other\n  endpoint", 1)
    )
    with pytest.raises(ConfigError):
        Config.load(repo, env=env)


# TC-C-009
def test_tc_c_009_futures_categories(config: Config, tmp_path: Path) -> None:
    committed = Config.load(REPO, env={"QUANT_CN_LAKE_ROOT": str(tmp_path)})
    pairs = {(c.exchange, c.broker) for c in committed.futures_categories}
    assert ("DCE", "期货公司会员") in pairs and len(pairs) == len(committed.futures_categories)
    assert config.futures_categories == []  # fixture repo has no futures_categories.yaml


# TC-C-010
def test_tc_c_010_ticker_aliases(config: Config, tmp_path: Path) -> None:
    committed = Config.load(REPO, env={"QUANT_CN_LAKE_ROOT": str(tmp_path)})
    pairs = {(a.old_code, a.new_code) for a in committed.ticker_aliases}
    assert ("000043.SZ", "001914.SZ") in pairs and len(pairs) == 3
    assert config.ticker_aliases == []


# TC-C-011
def test_tc_c_011_universe(config: Config) -> None:
    assert config.universe.min_sessions == 120 and config.universe.exchanges == ["SH", "SZ"]
    assert Config.model_fields["universe"].default_factory is not None


# TC-C-012
def test_tc_c_012_factors(config: Config, tmp_path: Path) -> None:
    committed = Config.load(REPO, env={"QUANT_CN_LAKE_ROOT": str(tmp_path)})
    names = {f.name: f.class_name for f in committed.factors}
    assert len(names) == 6 and names["momentum_12_1"] == "MomentumFactor"
    assert config.factors == []
