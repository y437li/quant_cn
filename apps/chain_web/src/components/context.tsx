import { createContext, useContext } from "react";
import type { Bootstrap } from "../api/client";
import type { Taxonomy } from "../graph/taxonomy";

/** Purpose: what every view needs: reference data, the taxonomy index and navigation. */
export type Selection = { kind: "company" | "node" | "sector"; id: string };
export interface AppCtx { boot: Bootstrap; tx: Taxonomy; select: (s: Selection) => void }
export const Ctx = createContext<AppCtx | null>(null);
export function useApp(): AppCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error("useApp outside provider");
  return c;
}
