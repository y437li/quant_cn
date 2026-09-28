"""Outcome record of one pipeline step or fetcher run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StepStatus = Literal["ok", "blocked", "failed", "dry_run"]


@dataclass
class StepReport:
    """
    Purpose:
        Counts and status of one step (usually one dataset's fetch) so runs can be summarised.

    Contract:
        Input:
            name:       str         -- step or dataset name
            status:     StepStatus  -- "ok" | "blocked" | "failed" | "dry_run"
            keys_total: int >= 0    -- keys considered
            fetched:    int >= 0    -- keys fetched with rows
            skipped:    int >= 0    -- keys already done
            empty:      int >= 0    -- keys fetched with zero rows
            rows:       int >= 0    -- rows written
            message:    str         -- reason for blocked/failed, or dry-run detail
        Output:
            mutable dataclass
        Raises:
            (none)

    Used by:
        core.BaseFetcher.run           -- returned per dataset run
        core.BaseStep.run              -- return type
        lake.Compactor.rebuild         -- returned per dataset compaction
        pipeline.LocalRunner.run       -- collected into PipelineReport
        pipeline.DownloadPipeline.run  -- dry-run reports
        pipeline.FetchStep             -- injected type or call
        pipeline.PipelineReport        -- injected type or call
        pipeline.CompactStep           -- injected type or call
        pipeline.DeriveStep            -- injected type or call

    Test cases:
        TC-BF-001  fetch run counts fetched/skipped/empty correctly
    """

    name: str
    status: StepStatus = "ok"
    keys_total: int = 0
    fetched: int = 0
    skipped: int = 0
    empty: int = 0
    rows: int = 0
    message: str = ""
