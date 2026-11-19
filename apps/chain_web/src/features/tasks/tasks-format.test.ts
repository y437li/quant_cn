import { describe, expect, it } from "vitest";
import type { TaskStatus } from "../../api/client";
import { formatDuration, taskHeadline } from "./tasks-format";

describe("tasks format", () => {
  it("TC-TKF-001 durations", () => {
    expect(formatDuration(7.6)).toBe("8 秒");
    expect(formatDuration(185)).toBe("3 分 05 秒");
    expect(formatDuration(3720)).toBe("1 时 02 分");
  });

  it("TC-TKF-002 headline", () => {
    expect(taskHeadline({ last_run: null, steps: [] })).toBe("还没有运行记录：运行 make update-all。");
    const doc: TaskStatus = {
      last_run: {
        run_id: "r", trigger: "launchd", started_at: "2026-11-18 06:00:01", finished_at: "2026-11-18 06:40:00",
        counts: { ok: 1, failed: 1, skipped: 1 },
        steps: [
          { task: "a", status: "ok", duration_s: 1, exit_code: 0, as_of: null, note: "" },
          { task: "b", status: "failed", duration_s: 1, exit_code: 2, as_of: null, note: "x" },
          { task: "c", status: "skipped", duration_s: 0, exit_code: null, as_of: null, note: "" },
        ],
      },
      steps: [],
    };
    expect(taskHeadline(doc)).toBe("最近一次 11-18 06:00（自动）：1/3 成功，失败 1：b，跳过 1。");
  });
});
