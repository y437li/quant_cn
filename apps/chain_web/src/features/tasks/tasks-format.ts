import type { TaskStatus, TaskState } from "../../api/client";

export const STATE_LABEL: Record<TaskState, string> = { ok: "成功", failed: "失败", skipped: "跳过" };

/** Purpose: seconds as "8 秒" / "3 分 05 秒" / "1 时 02 分". Contract: pure; rounds to whole seconds. */
export function formatDuration(s: number): string {
  const t = Math.round(s);
  if (t < 60) return `${t} 秒`;
  if (t < 3600) return `${Math.floor(t / 60)} 分 ${String(t % 60).padStart(2, "0")} 秒`;
  return `${Math.floor(t / 3600)} 时 ${String(Math.floor((t % 3600) / 60)).padStart(2, "0")} 分`;
}

/** Purpose: the headline of the latest run: "最近一次 11-18 06:00（自动）：17/19 成功，失败 2：a、b". Contract: no run → "还没有运行记录". */
export function taskHeadline(doc: TaskStatus): string {
  const r = doc.last_run;
  if (!r) return "还没有运行记录：运行 make update-all。";
  const n = r.steps.length;
  const failed = r.steps.filter((s) => s.status === "failed").map((s) => s.task);
  const skipped = r.counts.skipped ? `，跳过 ${r.counts.skipped}` : "";
  const when = `${r.started_at.slice(5, 16)}（${r.trigger === "launchd" ? "自动" : "手动"}）`;
  return `最近一次 ${when}：${r.counts.ok}/${n} 成功` + (failed.length ? `，失败 ${failed.length}：${failed.join("、")}` : "") + `${skipped}。`;
}
