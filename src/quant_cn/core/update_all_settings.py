"""Settings of `update-all`: the daily update steps in order (plan 38, D-181)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from quant_cn.core.exceptions import ConfigError

FILE = Path("config") / "update_all.yaml"
_TARGET = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", re.MULTILINE)


class UpdateStep(BaseModel):
    """
    Purpose:
        One update step: its name, the make target it runs, the steps that must succeed first,
        the APP_DATA JSON file whose `as_of` is recorded, a timeout and extra attempts.

    Contract:
        Input:
            name, target: str (non-empty); needs: list[str]; output: str | None;
            timeout_min: int > 0 | None (None = the settings default); retry: int in [0, 3]
        Output:
            frozen pydantic model
        Raises:
            pydantic.ValidationError  -- missing field, extra keys, bad values

    Used by:
        core.UpdateAllSettings     -- field steps
        pipeline.UpdateAllRunner   -- runs each step

    Test cases:
        TC-UAS-001  config/update_all.yaml loads; every target exists in the Makefile
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    name: str = Field(min_length=1)
    target: str = Field(min_length=1)
    needs: list[str] = []
    output: str | None = None
    timeout_min: int | None = Field(default=None, gt=0)
    retry: int = Field(default=0, ge=0, le=3)


class UpdateAllSettings(BaseModel):
    """
    Purpose:
        The ordered update steps of `update-all` from `config/update_all.yaml`, with the default
        timeout, the output lines kept for a failed step and the runs per step in the status file.

    Contract:
        Input:
            steps: list[UpdateStep], unique names, each `needs` naming an earlier step;
            default_timeout_min, tail_lines, history: int > 0
        Output:
            frozen pydantic model; `load(repo_root)`, `find_missing_targets(makefile)`,
            `list_steps(only, start)`, `get_timeout_s(step)`
        Raises:
            pydantic.ValidationError  -- duplicate names, unknown or later `needs`

    Used by:
        pipeline.UpdateAllRunner  -- steps, timeouts, tail length
        cli.UpdateCommands        -- `update-all` command

    Test cases:
        TC-UAS-001  config/update_all.yaml loads; every target exists in the Makefile
        TC-UAS-002  duplicate names, unknown needs and a need on a later step are refused; a
                    missing or invalid file raises ConfigError
        TC-UAS-003  list_steps: only / start pick steps in config order; unknown names raise
                    ConfigError; get_timeout_s uses the step value, else the default
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    steps: list[UpdateStep] = Field(min_length=1)
    default_timeout_min: int = Field(default=30, gt=0)
    tail_lines: int = Field(default=20, gt=0)
    history: int = Field(default=10, gt=0)

    @model_validator(mode="after")
    def _check(self) -> UpdateAllSettings:
        seen: set[str] = set()
        for step in self.steps:
            if step.name in seen:
                raise ValueError(f"duplicate step name: {step.name}")
            later = [n for n in step.needs if n not in seen]
            if later:
                raise ValueError(f"step {step.name} needs unknown or later steps: {later}")
            seen.add(step.name)
        return self

    @classmethod
    def load(cls, repo_root: Path) -> UpdateAllSettings:
        """
        Purpose:
            Read `config/update_all.yaml`.

        Contract:
            Input:
                repo_root: Path
            Output:
                UpdateAllSettings
            Raises:
                ConfigError  -- missing file, unreadable YAML or invalid content
        """
        path = repo_root / FILE
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return cls(**data)
        except (OSError, yaml.YAMLError, TypeError, ValidationError) as exc:
            raise ConfigError(f"invalid update-all settings {path}: {exc}") from exc

    def find_missing_targets(self, makefile: Path) -> list[str]:
        """
        Purpose:
            The step targets that the Makefile does not define.

        Contract:
            Input:
                makefile: Path
            Output:
                list[str]  -- in step order; [] when all exist
            Raises:
                ConfigError  -- the Makefile cannot be read
        """
        try:
            defined = set(_TARGET.findall(makefile.read_text(encoding="utf-8")))
        except OSError as exc:
            raise ConfigError(f"cannot read {makefile}: {exc}") from exc
        return [s.target for s in self.steps if s.target not in defined]

    def list_steps(
        self, only: list[str] | None = None, start: str | None = None
    ) -> list[UpdateStep]:
        """
        Purpose:
            The steps to run: all, only the named ones, or from `start` on; config order kept.

        Contract:
            Input:
                only:  list[str] | None  -- step names
                start: str | None        -- first step name
            Output:
                list[UpdateStep]
            Raises:
                ConfigError  -- an unknown step name
        """
        names = [s.name for s in self.steps]
        unknown = [n for n in [*(only or []), *([start] if start else [])] if n not in names]
        if unknown:
            raise ConfigError(f"unknown update steps: {unknown}; known: {names}")
        steps = self.steps[names.index(start) :] if start else list(self.steps)
        return [s for s in steps if not only or s.name in only]

    def get_timeout_s(self, step: UpdateStep) -> int:
        """
        Purpose:
            The step's time limit in seconds.

        Contract:
            Input:
                step: UpdateStep
            Output:
                int
            Raises:
                (none)
        """
        return 60 * (step.timeout_min or self.default_timeout_min)
