"""App Store developer accounts mapped to companies (plan 19 ph2)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "app_publishers.yaml"
A_SHARE = (".SH", ".SZ", ".BJ")  # ts_code suffixes of mainland listings


class AppPublisher(BaseModel):
    """
    Purpose:
        One App Store seller account (artist_id) and the company behind it.

    Contract:
        Input:
            artist_id: str; artist: str (account name as the store shows it); company: str;
            code: str | None  -- listed ts_code (A or HK), None when not listed
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- missing field, extra keys

    Used by:
        core.AppPublisherSettings  -- field publishers

    Test cases:
        TC-APS-001  config/app_publishers.yaml loads; artist ids are unique
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    artist_id: str
    artist: str
    company: str
    code: str | None = None


class AppPublisherSettings(BaseModel):
    """
    Purpose:
        The App Store publisher map of `config/app_publishers.yaml` (plan 19 ph2): artist_id ->
        company and listed code, so chart rows can be read per company.

    Contract:
        Input:
            publishers: list[AppPublisher] (>= 1, unique artist_id)
        Output:
            frozen pydantic model; `load(repo_root)` (classmethod); `get_by_artist() -> dict`;
            `get_a_share() -> dict` (ts_code -> company of every A-share listed company)
        Raises:
            ConfigError  -- unreadable YAML, invalid content, duplicate artist_id or no file

    Used by:
        portfolio.AppRankReader  -- company of each chart row
        cli.AppServiceBuilder  -- `build_sector_monitor` loads it

    Test cases:
        TC-APS-001  config/app_publishers.yaml loads; artist ids are unique; 巨人 maps to
                    002558.SZ; get_a_share holds A-share codes only
        TC-APS-002  a duplicate artist_id or a missing file raises ConfigError
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    publishers: list[AppPublisher] = Field(min_length=1)

    @classmethod
    def load(cls, repo_root: Path) -> AppPublisherSettings:
        """
        Purpose:
            Read `config/app_publishers.yaml`.

        Contract:
            Input:
                repo_root: Path
            Output:
                AppPublisherSettings
            Raises:
                ConfigError  -- unreadable YAML, invalid content, duplicate artist_id or no file
        """
        path = repo_root / FILE
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            settings = cls(**raw)
        except (OSError, yaml.YAMLError, TypeError, ValidationError) as exc:
            raise ConfigError(f"invalid app publisher map {path}: {exc}") from exc
        ids = [p.artist_id for p in settings.publishers]
        if len(set(ids)) != len(ids):
            raise ConfigError(f"duplicate artist_id in {path}")
        return settings

    def get_by_artist(self) -> dict[str, AppPublisher]:
        """
        Purpose:
            The map keyed by artist_id.

        Contract:
            Input:
                (none)
            Output:
                dict[str, AppPublisher]
            Raises:
                (none)
        """
        return {p.artist_id: p for p in self.publishers}

    def get_a_share(self) -> dict[str, str]:
        """
        Purpose:
            Every A-share listed company of the map.

        Contract:
            Input:
                (none)
            Output:
                dict[str, str]  -- ts_code -> company; HK / unlisted companies left out
            Raises:
                (none)
        """
        return {p.code: p.company for p in self.publishers if p.code and p.code.endswith(A_SHARE)}
