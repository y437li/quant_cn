"""Checks release-lag rules against observed official release dates (D-086)."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from quant_cn.core.dataset_spec import DatasetSpec
from quant_cn.lake.lake_query import LakeQuery

CHECK_COLUMNS = ["dataset", "rule_days", "releases", "observed_max", "later_than_rule", "latest"]
PERIOD_DAY = 25  # a release on or after this day belongs to its own month (PMI, month-end release)


class ReleaseLagChecker:
    """
    Purpose:
        For every dataset with `known_on_rule: period_end_lag` and `release_dates` set, measure the
        observed lag (release date - period end) in that curated release-date dataset and count
        releases that came later than the rule. A rule earlier than any observed release is
        look-ahead; D-086 raises it to the observed maximum and `make check` warns if it recurs.
        The period of a release is the last month end before it, or its own month end when the
        release falls on/after day 25 (month-end PMI releases).

    Contract:
        Input:
            query:    LakeQuery                  -- curated release-date datasets
            datasets: Mapping[str, DatasetSpec]  -- Config.datasets
            since:    str                        -- YYYYMMDD; earlier rows use placeholder dates
        Output:
            instance; `compute`, `build_lines`
        Raises:
            (none at construction)

    Used by:
        cli.ResearchCommands  -- injected type or call

    Test cases:
        TC-RLC-001  a release later than the rule is counted; observed max reported
        TC-RLC-002  datasets without release_dates, or with the table missing, are skipped
        TC-RLC-003  build_lines gives one line per dataset, WARNING when a rule is too early
    """

    def __init__(
        self, query: LakeQuery, datasets: Mapping[str, DatasetSpec], since: str = "20100101"
    ) -> None:
        self._query = query
        self._datasets = dict(datasets)
        self._since = since

    def compute(self) -> pd.DataFrame:
        """
        Purpose:
            One row per checked dataset.

        Contract:
            Input:
                (none)
            Output:
                DataFrame  -- CHECK_COLUMNS; later_than_rule > 0 means the rule is too early
            Raises:
                LakeError  -- query failure
        """
        rows = []
        for spec in self._datasets.values():
            source = spec.release_dates
            if not source or not self._query.has_view(f"curated.{source}"):
                continue
            stats = self._query.sql(self._build_sql(source, spec.release_lag_days))
            record = stats.to_dict("records")[0]
            rows.append({"dataset": spec.name, "rule_days": spec.release_lag_days, **record})
        return pd.DataFrame(rows, columns=CHECK_COLUMNS)

    @staticmethod
    def build_lines(frame: pd.DataFrame) -> list[str]:
        """
        Purpose:
            Human-readable lines of a compute() result.

        Contract:
            Input:
                frame: DataFrame  -- compute() output
            Output:
                list[str]  -- "<dataset>: rule Nd, observed max Md over K releases -> ok"
                              (or "-> WARNING: n release(s) later than the rule")
            Raises:
                (none)
        """
        lines = []
        for row in frame.to_dict("records"):
            late = int(row["later_than_rule"])
            flag = f"WARNING: {late} release(s) later than the rule" if late else "ok"
            lines.append(
                f"{row['dataset']}: rule {row['rule_days']}d, observed max {row['observed_max']}d"
                f" over {row['releases']} releases -> {flag}"
            )
        return lines

    def _build_sql(self, source: str, rule: int) -> str:
        return f"""
            WITH r AS (SELECT strptime(release_date, '%Y%m%d')::DATE AS rd FROM curated.{source}
                       WHERE release_date >= '{self._since}'
                         AND substr(release_date, 7, 2) <> '01'),
            p AS (SELECT rd, CASE WHEN day(rd) >= {PERIOD_DAY} THEN last_day(rd)
                                  ELSE last_day(rd - INTERVAL 1 MONTH) END AS period_end FROM r)
            SELECT count(*) AS releases, coalesce(max(rd - period_end), 0) AS observed_max,
                   count(*) FILTER (WHERE rd - period_end > {rule}) AS later_than_rule,
                   coalesce(strftime(max(rd), '%Y%m%d'), '') AS latest
            FROM p"""
