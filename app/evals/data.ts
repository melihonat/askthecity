// The /evals data, written by `python -m evals results` from the committed runs (evals/results.py).
// Display-ready: every number is formatted there, so the page, README and RESULTS.md agree.
import results from "./results.json";

export type Cell = { text: string; mark: "gain" | "same" | null };
export type Row = { rung: string; why: string; highlight: boolean; run: string; cells: Cell[] };

export type EvalsData = {
  intro: { questions: number; refuse: number } | null;
  headerLink: string;
  columns: { key: string; label: string; n: string }[];
  ladder: Row[];
  side: Row[];
  shipBar: { rung: string; unmet: string[] } | null;
  agreement: { agree: number; total: number; contradictionsMissed: number } | null;
  underTable: string;
};

export const EVALS = results as EvalsData;
