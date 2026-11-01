// Static (UI.md, "/evals"): rendered at build time from the committed run data, no DB or Gateway call,
// so it costs $0 and works in every limit state.
import type { Metadata } from "next";
import { SiteHeader } from "../site-header";
import { EVALS, type Cell, type Row } from "./data";

export const dynamic = "error";
export const metadata: Metadata = { title: "Evals · Ask the City" };

const REPO = "https://github.com/melihonat/askthecity/blob/main";

function Value({ cell }: { cell: Cell }) {
  if (cell.mark === "gain") return <strong>{cell.text}</strong>;
  if (cell.mark === "same")
    return (
      <>
        <span className="muted" title="inside the run-to-run spread">
          ≈
        </span>{" "}
        {cell.text}
      </>
    );
  return <>{cell.text}</>;
}

function Table({ rows, caption }: { rows: Row[]; caption: string }) {
  return (
    <table className="evals">
      <caption>{caption}</caption>
      <thead>
        <tr>
          <th scope="col">Rung</th>
          {EVALS.columns.map((c) => (
            <th scope="col" key={c.key}>
              {c.label}
              <span className="muted">n {c.n}</span>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.run} className={r.highlight ? "shipped" : undefined}>
            <th scope="row">
              <code>{r.rung}</code>
              {r.highlight && <span className="bar"> ✓ ship bar</span>}
              <span className="muted">{r.why}</span>
            </th>
            {r.cells.map((cell, i) => (
              <td key={EVALS.columns[i].key}>
                <Value cell={cell} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function EvalsPage() {
  return (
    <>
      <SiteHeader current="evals" />
      <main className="evals-page">
        {EVALS.intro ? (
          <p>
            {EVALS.intro.questions} questions written before the first build, {EVALS.intro.refuse} of them meant to
            be refused. Each row adds one thing to the row above, all run on the same final code.
          </p>
        ) : (
          <p>No eval run has been published yet.</p>
        )}
        {EVALS.ladder.length > 0 && (
          <>
            <Table rows={EVALS.ladder} caption="Main ladder" />
            {EVALS.fixNote && <p>{EVALS.fixNote}</p>}
            <p className="muted">{EVALS.underTable}</p>
          </>
        )}
        {EVALS.side.length > 0 && (
          <>
            <p>Alternatives tried against shipped, one change each.</p>
            <Table rows={EVALS.side} caption="Side table" />
          </>
        )}
        <p className="muted">
          All columns in <a href={`${REPO}/evals/RESULTS.md`}>RESULTS.md</a> · how they&apos;re scored in{" "}
          <a href={`${REPO}/EVALS.md`}>EVALS.md</a> · the pre-registered rungs in{" "}
          <a href={`${REPO}/evals/LADDER.md`}>LADDER.md</a>
        </p>
      </main>
    </>
  );
}
