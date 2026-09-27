from __future__ import annotations

from tests.support import MiniLake


# TC-RL-001
def test_tc_rl_001_rows_queryable(lake: MiniLake) -> None:
    run = lake.run_log.start_run("download")
    lake.run_log.event(run, "daily", "20260828", "fetched", 10, 5)
    lake.run_log.finish_run(run, "ok")
    df = lake.query.sql(
        "SELECT dataset, status, n_rows FROM meta.run_log WHERE run_id = ? "
        "ORDER BY dataset NULLS FIRST",
        [run],
    )
    assert df["status"].tolist() == ["ok", "fetched"]
    assert df["n_rows"].tolist() == [0, 10]


# TC-RL-002
def test_tc_rl_002_unique_ids_and_finish(lake: MiniLake) -> None:
    a, b = lake.run_log.start_run("x"), lake.run_log.start_run("x")
    assert a != b
    lake.run_log.finish_run(a, "failed", "boom")
    row = lake.query.sql(
        "SELECT status, message, finished_at FROM meta.run_log WHERE run_id = ?", [a]
    )
    assert row["status"].iloc[0] == "failed" and row["message"].iloc[0] == "boom"
    assert row["finished_at"].notna().all()
