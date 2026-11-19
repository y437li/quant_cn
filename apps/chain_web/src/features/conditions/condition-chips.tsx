import type { ConditionResult } from "../../api/client";
import { conditionTitle, stateMark } from "./condition-format";

/**
 * Purpose: one chip per structured condition (plan 15 ph7f): green met, red unmet, grey unknown; tooltip with value and threshold.
 * Contract: empty list renders nothing.
 */
export function ConditionChips({ items }: { items: ConditionResult[] }) {
  if (items.length === 0) return null;
  return (
    <ul className="cd-chips">{items.map((c, i) => (
      <li key={i} className={`cd-chip ${c.state}`} title={conditionTitle(c)} data-state={c.state}>
        <b>{stateMark(c)}</b> {c.required && <span className="cd-req" title="必须满足">必</span>}{c.label}
      </li>))}
    </ul>
  );
}
