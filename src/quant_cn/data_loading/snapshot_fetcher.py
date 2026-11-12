"""Sweep for sources that only serve the current state (App Store charts, D-137): today only."""

from __future__ import annotations

from quant_cn.data_loading.fetchers import EnumFetcher


class SnapshotFetcher(EnumFetcher):
    """
    Purpose:
        Capture a source that has no history (the vendor only serves "now"): one key per value
        for today's date, "<today>_<value>", with today from the injected Clock. The run's start
        and end are ignored, so past dates are never requested and a missed day stays missing.
        `sweep.key_field` (the capture date) is filled from the key's date part by BaseFetcher.

    Contract:
        Input:
            EnumFetcher dependencies (spec, client, store, fetch_log, run_log, clock, values)
        Output:
            instance; keys -> ["<YYYYMMDD>_<value>", ...] in values order;
            params -> {sweep.param: value} + extra_params
        Raises:
            (none)

    Used by:
        data_loading.FetcherFactory.build  -- sweep kind "snapshot"

    Test cases:
        TC-SNF-001  keys are today's date joined to each value; run range ignored
        TC-SNF-002  params carry the value (not the date) and the extra params
        TC-SNF-003  a run writes one raw file per key with the capture date filled; a second run
                    the same day skips the done keys, a forced run replaces them
    """

    def list_keys(self, start: str, end: str) -> list[str]:
        """
        Purpose:
            Today's keys, one per value.

        Contract:
            Input:
                start: str; end: str  -- ignored (no history at the source)
            Output:
                list[str]  -- "<YYYYMMDD>_<value>"
            Raises:
                (none)
        """
        today = self._clock.get_today()
        return [f"{today}_{value}" for value in super().list_keys(start, end)]

    def build_params(self, key: str, start: str, end: str) -> dict[str, str]:
        """
        Purpose:
            The value part of the key under the sweep parameter, plus the constant parameters.

        Contract:
            Input:
                key: str  -- "<YYYYMMDD>_<value>"; start: str; end: str -- ignored
            Output:
                dict[str, str]
            Raises:
                (none)
        """
        out = dict(self.spec.sweep.extra_params)
        out[str(self.spec.sweep.param)] = key.partition("_")[2]
        return out
