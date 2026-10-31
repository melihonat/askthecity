"use client";

import { useState } from "react";
import { parseBody } from "@/lib/ask/body";
import { MAX_QUESTION } from "@/lib/ask/config";
import { splitGap } from "@/lib/ask/gap";
import { EXAMPLES } from "@/lib/ask/scope";
import type { AskEvent, AskResponse, PassageView } from "@/lib/ask/types";

// Fixed per reason (CONTRACT.md, "Refusal rule"): no model-written text in a refusal.
const REFUSAL = {
  below_threshold: { line: "Nothing in the snapshot comes close to this question.", nearest: "Closest passages (not a match)" },
  model_declined: { line: "I found related passages, but none of them answers it.", nearest: "Related, but not an answer" },
  no_valid_citation: {
    line: "I couldn't back an answer with a citation, so I'm not giving one.",
    nearest: "Passages I had",
  },
} as const;

/** Single-turn: each question replaces the last one and its evidence. */
export function Ask() {
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [passages, setPassages] = useState<PassageView[] | null>(null);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(q = question) {
    if (!q.trim() || busy) return;
    setAsked(q.trim());
    setBusy(true);
    setPassages(null);
    setResponse(null);
    setError(null);
    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      if (!res.ok || !res.body) throw new Error((await res.json().catch(() => null))?.error ?? res.statusText);
      const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += value;
        let i;
        while ((i = buf.indexOf("\n")) >= 0) {
          const ev = JSON.parse(buf.slice(0, i)) as AskEvent | { type: "error"; message: string };
          buf = buf.slice(i + 1);
          if (ev.type === "passages") setPassages(ev.passages);
          else if (ev.type === "final") setResponse(ev.response);
          else if (ev.type === "error") setError(ev.message);
        }
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const cited =
    response?.kind === "answer"
      ? response.citations.map((c) => response.passages.find((p) => p.n === c.n)!)
      : [];
  const uncited = response?.kind === "answer" ? response.passages.filter((p) => !cited.includes(p)) : [];
  const answer = response?.kind === "answer" ? splitGap(response.text) : null;

  return (
    <main className="panes">
      <section className="ask">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="How late can my neighbour run a leaf blower?"
            aria-label="Your question"
            rows={3}
          />
          <div className="row">
            <span className={question.length > MAX_QUESTION ? "counter over" : "counter"}>
              {question.length} / {MAX_QUESTION}
            </span>
            <button type="submit" disabled={busy}>
              {busy ? "Asking…" : "Ask"}
            </button>
          </div>
        </form>

        <div className="chips">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.question}
              type="button"
              className={ex.trick ? "chip trick" : "chip"}
              disabled={busy}
              onClick={() => {
                setQuestion(ex.question);
                submit(ex.question);
              }}
            >
              {ex.question}
              {ex.trick && <span className="muted"> · try a trick</span>}
            </button>
          ))}
        </div>

        {asked && <h2 className="asked">{asked}</h2>}
        {busy && passages && <p className="muted">Found {passages.length} passages. Writing an answer from them…</p>}
        {error && <p className="error">{error}</p>}

        {response?.kind === "answer" && (
          <p className="answer">
            {answer!.body}
            {answer!.gap && <span className="gap"> {answer!.gap}</span>}
          </p>
        )}

        {response?.kind === "refusal" && (
          <>
            <p className="answer">
              <strong>The documents don&apos;t cover this.</strong>
            </p>
            <p>{REFUSAL[response.reason].line}</p>
            <p className="muted">{response.scope}</p>
          </>
        )}

        {response?.kind === "limit" && <p className="notice">That question is over 300 characters. Shorten it and ask again.</p>}
      </section>

      <aside className="sources">
        {response?.kind === "answer" && (
          <>
            <h3>Cited ({cited.length})</h3>
            {cited.map((p) => (
              <Card key={p.n} p={p} />
            ))}
            {uncited.length > 0 && (
              <details>
                <summary>{uncited.length} more retrieved, not cited</summary>
                {uncited.map((p) => (
                  <Card key={p.n} p={p} dim />
                ))}
              </details>
            )}
          </>
        )}

        {response?.kind === "refusal" && (
          <>
            <h3>{REFUSAL[response.reason].nearest}</h3>
            {response.nearest.map((p) => (
              <Card key={p.n} p={p} dim />
            ))}
          </>
        )}
      </aside>
    </main>
  );
}

function Card({ p, dim }: { p: PassageView; dim?: boolean }) {
  return (
    <article className={["card", p.companion && "companion", dim && "dim"].filter(Boolean).join(" ")}>
      <div>
        <span className="tag">{p.n}</span> <strong>{p.label}</strong>
        {p.amendedSince.length > 0 && (
          <span className="badge amber">amended since by {p.amendedSince.map((n) => `By-law ${n}`).join(", ")}</span>
        )}
        {p.notYetLaw && <span className="badge red">not yet law</span>}
        {p.companion && (
          <span className="badge violet">{p.notYetLaw ? "replacement for a retrieved §" : "amendment to a retrieved §"}</span>
        )}
      </div>
      <div className="muted">
        {p.sublabel} ·{" "}
        <a href={p.href} target="_blank" rel="noreferrer">
          source ↗
        </a>
      </div>
      <div className="body">
        {parseBody(p.body).map((b, i) =>
          b.kind === "text" ? (
            <p key={i}>{b.text}</p>
          ) : (
            <table key={i}>
              <thead>
                <tr>
                  {b.header.map((h, j) => (
                    <th key={j}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {b.rows.map((r, j) => (
                  <tr key={j}>
                    {r.map((c, k) => (
                      <td key={k}>{c}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ),
        )}
      </div>
    </article>
  );
}
