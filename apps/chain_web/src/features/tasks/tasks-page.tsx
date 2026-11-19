import { useEffect, useState } from "react";
import { api, type TaskStatus } from "../../api/client";
import { STATE_LABEL, formatDuration, taskHeadline } from "./tasks-format";

/**
 * Purpose: the 更新状态 page at #tasks (plan 38, D-181): the latest `update-all` run (every step with state, time,
 * data date and the last output line of a failure) and per step its last success and recent runs.
 * Contract: read-only display of GET /api/tasks; no document → empty state with the command to run.
 */
export function TasksPage() {
  const [doc, setDoc] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.getTasks().then(setDoc).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="wl-page" data-empty="tasks"><p className="wl-empty">更新状态没有加载出来：{error}。先运行 <code>make update-all</code>。</p></div>;
  if (!doc) return <div className="wl-page"><p className="wl-empty">正在加载…</p></div>;
  const last = new Map((doc.last_run?.steps ?? []).map((s) => [s.task, s]));
  return (
    <div className="wl-page mc-page" data-page="tasks">
      <div className="wl-head"><h2>更新状态</h2><p>{taskHeadline(doc)}</p></div>
      <section className="wl-section">
        <div className="fm-scroll">
          <table className="fm-table tk-table">
            <thead><tr><th>步骤</th><th>最近一次</th><th>用时</th><th>数据日期</th><th>上次成功</th><th>最近几次</th><th>说明</th></tr></thead>
            <tbody>
              {doc.steps.map((s) => {
                const r = last.get(s.task);
                return (
                  <tr key={s.task} data-task={s.task}>
                    <td>{s.task}</td>
                    <td className={`tk-state ${r?.status ?? s.status ?? "none"}`}>{r ? STATE_LABEL[r.status] : s.status ? STATE_LABEL[s.status] : "未运行"}</td>
                    <td>{r ? formatDuration(r.duration_s) : "—"}</td>
                    <td>{s.as_of ?? "—"}</td>
                    <td>{s.last_ok_at?.slice(5, 16) ?? "—"}</td>
                    <td className="tk-dots">{s.history.slice().reverse().map((h) => <span key={h.run_id} className={`tk-dot ${h.status}`} title={`${h.run_id} ${STATE_LABEL[h.status]} ${formatDuration(h.duration_s)}`} />)}</td>
                    <td className="tk-note" title={r?.note ?? ""}>{r?.note ?? ""}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      <p className="wl-note">每天 06:00 自动运行 make update-all（也可以手动运行）。某一步失败不会中断，依赖它的步骤跳过；每一步都记在数据湖 meta/task_log。数据日期取自该步骤输出文件的 as_of。</p>
    </div>
  );
}
