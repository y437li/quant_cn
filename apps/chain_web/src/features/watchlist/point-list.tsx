import { splitPoints } from "./watchlist-format";

/** Purpose: a reason text as a bullet list (one point → plain text). Contract: empty text renders nothing. */
export function PointList({ text }: { text: string | null | undefined }) {
  const pts = splitPoints(text);
  if (!pts.length) return null;
  if (pts.length === 1) return <span>{pts[0]}</span>;
  return <ul className="pt-list">{pts.map((p, i) => <li key={i}>{p}</li>)}</ul>;
}

/** Purpose: a titled block (理由 / 要盯的信号) with the text as bullets. Contract: empty text renders nothing. */
export function Points({ title, text }: { title: string; text: string | null | undefined }) {
  if (!splitPoints(text).length) return null;
  return <div className="note pt-block"><strong>{title}</strong><PointList text={text} /></div>;
}
