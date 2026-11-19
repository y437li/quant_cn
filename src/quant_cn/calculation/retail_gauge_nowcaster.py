"""Daily RetailGauge readings: training, walk-forward, calibration, streaks (plan 21 ph3)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import pandas as pd

from quant_cn.calculation.holder_count_panel import HolderCountPanel
from quant_cn.calculation.retail_gauge_feature_builder import KEY_COLUMNS, RetailGaugeFeatureBuilder
from quant_cn.calculation.retail_gauge_model import RetailGaugeModel
from quant_cn.core.exceptions import LakeError
from quant_cn.core.retail_gauge_settings import RetailGaugeSettings
from quant_cn.lake.dated_table_store import DatedTableStore
from quant_cn.lake.parquet_writer import ParquetWriter

TABLE = "retail_gauge"
GAUGE_COLUMNS = [
    "ts_code",
    "as_of",
    "q",
    "pct",
    "exp_change",
    "iqr_lo",
    "iqr_hi",
    "avoid",
    "lo_streak",
    "hi_streak",
    "retail_leaving",
    "avoid_strong",
    "model_version",
]
BACKTEST = "reports/retail_gauge/backtest.parquet"
CALIBRATION = "reports/retail_gauge/calibration.parquet"
DECILES = 10


class RetailGaugeNowcaster:
    """
    Purpose:
        Turn RetailGauge features into daily readings (plan 21 ph3, D-142, D-155, D-167):
        - `build_model(key)`: fit on quarter-end rows of quarters before `key` whose holder counts
          were announced by `key`; the model is saved under model_root/<model_version>/<key>.
          Daily readings use the model of the last retrain key on or before the as-of date
          (the 1st of each `retrain_months` month, after a reporting season).
        - `run_walk_forward(end)`: expanding walk-forward at every quarter end from the
          (min_train_quarters + 1)-th quarter (labels announced by that quarter end), written
          to derived/reports/retail_gauge/backtest.parquet; `compute_calibration` maps pct
          deciles to the realised change relative to the quarter's median (25 / 50 / 75%).
        - `run(as_ofs)`: pct, the calibrated expected change and IQR, avoid (pct >=
          avoid_pct), and the D-167 streaks: readings at t, t - step, t - 2 step ... sessions
          in the same quarter on the same side (<= leaving_pct / >= avoid_pct); a missing
          checkpoint ends the streak; retail_leaving / avoid_strong = streak >= persist_n.
          Rows go to derived/retail_gauge (one file per year; reruns replace their as_of).

    Contract:
        Input:
            settings:   RetailGaugeSettings
            features:   RetailGaugeFeatureBuilder
            holders:    HolderCountPanel
            writer:     ParquetWriter  -- write_table (backtest)
            tables:     DatedTableStore  -- derived/retail_gauge, gauge history, backtest
            model_root: Path           -- folder of saved models
            new_model:  Callable[[], RetailGaugeModel]
        Output:
            instance; `build_model`, `run_walk_forward`, `compute_calibration`, `run`,
            `get_retrain_key`, `compute_streaks` (static)
        Raises:
            LakeError  -- fewer than min_train_quarters labelled quarters, or no calibration

    Used by:
        cli.GaugeCommands  -- `retail-gauge`, `retail-gauge-backtest`

    Test cases:
        TC-RGN-001  get_retrain_key: the 1st of the last retrain month on or before as_of
                    (20250430 -> 20241101, 20250501 -> 20250501)
        TC-RGN-002  compute_streaks: 3 checkpoints in a row <= 0.3 -> retail_leaving, 2 do
                    not; a missing checkpoint resets; a new quarter starts a new streak;
                    avoid at 0.9 and not at 0.8999
        TC-RGN-003  build_model drops labels announced after the key (leakage: a future-dated label
                    changes nothing); fewer than min_train_quarters -> LakeError
        TC-RGN-004  compute_calibration: deciles of pct map to the quantiles of y minus the
                    quarter median, only labels announced by the key
    """

    def __init__(
        self,
        settings: RetailGaugeSettings,
        features: RetailGaugeFeatureBuilder,
        holders: HolderCountPanel,
        writer: ParquetWriter,
        tables: DatedTableStore,
        model_root: Path,
        new_model: Callable[[], RetailGaugeModel],
    ) -> None:
        self._s = settings
        self._features = features
        self._holders = holders
        self._writer = writer
        self._tables = tables
        self._root = model_root / settings.model_version
        self._new_model = new_model
        self._models: dict[str, RetailGaugeModel] = {}
        self._qe_rows = pd.DataFrame()
        self._qe_end = ""

    def build_model(self, key: str) -> RetailGaugeModel:
        """
        Purpose:
            Fit (or load, when already saved) the model of retrain key `key`.

        Contract:
            Input:
                key: str  -- YYYYMMDD
            Output:
                RetailGaugeModel  -- fitted
            Raises:
                LakeError  -- fewer than min_train_quarters labelled quarters
        """
        if key in self._models:
            return self._models[key]
        model, folder = self._new_model(), self._root / key
        if (folder / "meta.json").exists():
            model.load(folder)
        else:
            rows = self._get_labelled(key)
            train = rows[(rows["q"] < key) & (rows["ann_y"].fillna("99999999") <= key)]
            if train["q"].nunique() < self._s.min_train_quarters:
                raise LakeError(
                    f"RetailGauge: fewer than {self._s.min_train_quarters} quarters before {key}"
                )
            model.build(train, self._list_features(rows))
            model.save(folder)
        self._models[key] = model
        return model

    def run_walk_forward(self, end: str) -> pd.DataFrame:
        """
        Purpose:
            Out-of-sample quarter-end readings for every quarter with enough history.

        Contract:
            Input:
                end: str  -- YYYYMMDD, last quarter end included
            Output:
                DataFrame  -- ts_code, q, as_of, y, ann_y, pct; also written to BACKTEST, and
                              the quarter-end feature rows to derived/retail_gauge_features
            Raises:
                LakeError  -- write failed
        """
        rows = self._get_labelled(end)
        feats, quarters, out = self._list_features(rows), sorted(rows["q"].unique()), []
        for q in quarters[self._s.min_train_quarters :]:
            test = rows[rows["q"] == q]
            as_of = str(test["as_of"].iloc[0])
            train = rows[(rows["q"] < q) & (rows["ann_y"].fillna("99999999") <= as_of)]
            model = self._new_model()
            model.build(train, feats)
            part = test[["ts_code", "q", "as_of", "y", "ann_y"]].copy()
            part["pct"] = model.compute_pct(test)
            out.append(part)
        frame: pd.DataFrame = pd.concat(out, ignore_index=True)
        self._writer.write_table("derived", BACKTEST, frame)
        self._features.write(rows.drop(columns=["y", "ann_y"]))
        return frame

    def compute_calibration(self, backtest: pd.DataFrame, key: str) -> pd.DataFrame:
        """
        Purpose:
            Decile -> 25 / 50 / 75% of the realised change minus the quarter median, from
            walk-forward rows whose labels were announced by `key`.

        Contract:
            Input:
                backtest: DataFrame  -- run_walk_forward result
                key:      str        -- YYYYMMDD
            Output:
                DataFrame  -- index dec 0..9; iqr_lo, exp_change, iqr_hi, n
            Raises:
                LakeError  -- no labelled rows by key
        """
        known = backtest[backtest["y"].notna() & (backtest["ann_y"].fillna("99999999") <= key)]
        if known.empty:
            raise LakeError(f"RetailGauge: no calibration rows by {key}")
        rel = known["y"] - known.groupby("q")["y"].transform("median")
        dec = (known["pct"] * DECILES).astype(int).clip(upper=DECILES - 1)
        by = rel.groupby(dec.to_numpy())
        return pd.DataFrame(
            {
                "iqr_lo": by.quantile(0.25),
                "exp_change": by.median(),
                "iqr_hi": by.quantile(0.75),
                "n": by.size(),
            }
        )

    def run(self, as_ofs: Sequence[str]) -> pd.DataFrame:
        """
        Purpose:
            Daily readings for the as-of dates, written to derived/retail_gauge (the last
            as-of date's feature rows to derived/retail_gauge_features).

        Contract:
            Input:
                as_ofs: Sequence[str]  -- YYYYMMDD (mapped to the last session on or before)
            Output:
                DataFrame  -- GAUGE_COLUMNS for the as-of sessions
            Raises:
                LakeError  -- no walk-forward table, model or calibration for an as-of date
        """
        backtest = self._tables.read_report(BACKTEST)  # LakeError: run the walk-forward first
        rows = self._features.build(as_ofs)
        self._features.write(rows[rows["as_of"] == rows["as_of"].max()])
        parts = []
        for as_of, group in rows.groupby("as_of"):
            key = self.get_retrain_key(str(as_of))
            cal = self.compute_calibration(backtest, key)
            part = group[["ts_code", "as_of", "q"]].copy()
            part["pct"] = self.build_model(key).compute_pct(group)
            dec = (part["pct"] * DECILES).astype(int).clip(upper=DECILES - 1)
            for col in ("exp_change", "iqr_lo", "iqr_hi"):
                part[col] = cal[col].reindex(dec.to_numpy()).to_numpy()
            parts.append(part)
        new = pd.concat(parts, ignore_index=True)
        history = self._read_history(new)
        sessions = list(self._features.sessions)
        frame = self.compute_streaks(
            pd.concat([history, new], ignore_index=True), sessions, self._s
        )
        frame["model_version"] = self._s.model_version
        out = frame[frame["as_of"].isin(new["as_of"].unique())][GAUGE_COLUMNS].reset_index(
            drop=True
        )
        self._tables.write(TABLE, out, "as_of")
        return out

    def get_retrain_key(self, as_of: str) -> str:
        """
        Purpose:
            The retrain key of an as-of date: the 1st of the last retrain month on or before.

        Contract:
            Input:
                as_of: str  -- YYYYMMDD
            Output:
                str  -- YYYYMM01
            Raises:
                (none)
        """
        year = int(as_of[:4])
        keys = [f"{y}{m:02d}01" for y in (year - 1, year) for m in sorted(self._s.retrain_months)]
        return max(k for k in keys if k <= as_of)

    @staticmethod
    def compute_streaks(
        frame: pd.DataFrame, sessions: Sequence[str], settings: RetailGaugeSettings
    ) -> pd.DataFrame:
        """
        Purpose:
            avoid, lo_streak / hi_streak, retail_leaving / avoid_strong (D-155, D-167).

        Contract:
            Input:
                frame:    DataFrame  -- ts_code, as_of, q, pct (history and new rows)
                sessions: Sequence[str]  -- trading sessions, ascending
                settings: RetailGaugeSettings
            Output:
                DataFrame  -- frame plus the five columns
            Raises:
                (none)
        """
        s = settings
        pos = {d: i for i, d in enumerate(sessions)}
        out = frame.drop_duplicates(["ts_code", "as_of"], keep="last").copy()
        out["avoid"] = out["pct"] >= s.avoid_pct
        out["_i"] = out["as_of"].map(pos)
        pct = out.set_index(["ts_code", "q", "_i"])["pct"]
        for name, hit in (("lo_streak", pct <= s.leaving_pct), ("hi_streak", pct >= s.avoid_pct)):
            run = hit.astype(int)
            for k in range(1, s.persist_n):
                back = (
                    hit.reindex(
                        pd.MultiIndex.from_arrays(
                            [out["ts_code"], out["q"], out["_i"] - k * s.persist_step]
                        )
                    )
                    .fillna(False)
                    .to_numpy(dtype=bool)
                )
                run = run + (back & (run.to_numpy() == k)).astype(int)
            out[name] = run.to_numpy()
        out["retail_leaving"] = out["lo_streak"] >= s.persist_n
        out["avoid_strong"] = out["hi_streak"] >= s.persist_n
        return out.drop(columns="_i")

    def _get_labelled(self, end: str) -> pd.DataFrame:
        if end > self._qe_end:
            rows = self._features.build_quarter_ends(end)
            self._qe_rows = pd.concat([rows, self._holders.compute_labels(rows)], axis=1)
            self._qe_end = end
        out: pd.DataFrame = self._qe_rows[self._qe_rows["q"] <= end]
        return out

    def _list_features(self, rows: pd.DataFrame) -> list[str]:
        return [c for c in rows.columns if c not in (*KEY_COLUMNS, "y", "ann_y")]

    def _read_history(self, new: pd.DataFrame) -> pd.DataFrame:
        years = sorted({d[:4] for d in new["as_of"]} | {str(int(d[:4]) - 1) for d in new["as_of"]})
        old = self._tables.read(TABLE, years)
        if old.empty:
            return pd.DataFrame(columns=["ts_code", "as_of", "q", "pct"])
        keep = old["q"].isin(new["q"].unique()) & ~old["as_of"].isin(new["as_of"].unique())
        out: pd.DataFrame = old.loc[keep, ["ts_code", "as_of", "q", "pct"]]
        return out
